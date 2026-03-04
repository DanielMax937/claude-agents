import requests
import pandas as pd
import time
from datetime import datetime
import os

# --- 显示设置 ---
pd.set_option('display.max_rows', None)
pd.set_option('display.width', 2000)
pd.set_option('display.float_format', '{:.4f}'.format)

# --- 品种配置 ---
VARIETY_CONFIG = {
    "ni": {"variety": 10, "endpoint": 151, "name": "镍"},
    "ag": {"variety": 7, "endpoint": 151, "name": "白银"},
    "au": {"variety": 3, "endpoint": 151, "name": "黄金"},
    "sc": {"variety": 1, "endpoint": 163, "name": "原油"},
    "lc": {"variety": 2, "endpoint": 226, "name": "碳酸锂"},
}


def fetch_and_save_options(target_contract="ni2602"):
    """
    获取指定合约的完整期权链，展示 T型报价并保存到 CSV。
    支持品种: ni(镍), ag(白银), au(黄金), sc(原油), lc(集运指数)
    """
    # 1. 从合约代码提取品种
    import re
    match = re.match(r'([a-zA-Z]+)', target_contract)
    if not match:
        print(f"❌ 无法解析合约代码: {target_contract}")
        return

    variety_code = match.group(1).lower()

    if variety_code not in VARIETY_CONFIG:
        print(f"❌ 不支持的品种: {variety_code}")
        print(f"ℹ️ 支持的品种: {', '.join(VARIETY_CONFIG.keys())}")
        return

    config = VARIETY_CONFIG[variety_code]
    base_url = f"https://futsseapi.eastmoney.com/list/option/{config['endpoint']}"
    variety_id = config["variety"]
    variety_name = config["name"]

    # 请求所有核心字段 + Greeks + IV (yhbdl)
    extra_fields = "delta,gamma,vega,theta,rho,yhbdl"
    base_fields = "dm,p,ccl,vol,xqj"

    print(f"🚀 [1/4] 正在从东方财富抓取 [{target_contract}] ({variety_name}) 全量数据...")

    all_data = []
    page_index = 0

    # 2. 分页抓取循环
    while True:
        params = {
            "field": f"{base_fields},{extra_fields}",
            "orderBy": "dm",
            "sort": "asc",
            "pageSize": 100,
            "pageIndex": page_index,
            "variety": variety_id
        }

        try:
            resp = requests.get(base_url, params=params, timeout=5)
            if resp.status_code != 200:
                print(f"❌ 请求失败: HTTP {resp.status_code}")
                break

            data_list = resp.json().get('list', [])
            if not data_list:
                break

            all_data.extend(data_list)

            # 如果不满100条，说明是最后一页
            if len(data_list) < 100:
                break
            page_index += 1
            time.sleep(0.1)  # 防封限速

        except Exception as e:
            print(f"❌ 网络异常: {e}")
            break

    if not all_data:
        print("❌ 未获取到任何数据，请检查网络。")
        return

    # 3. 数据清洗与过滤
    print(f"🔄 [2/4] 数据清洗与 T型重构...")
    df = pd.DataFrame(all_data)

    # 提取标的 (如从 ni2602C100000 提取 ni2602)
    df['标的'] = df['dm'].str.extract(r'([a-zA-Z]+\d{4})')

    # 过滤掉非目标月份的数据
    df_target = df[df['标的'] == target_contract].copy()

    if df_target.empty:
        print(f"⚠️ 警告: API 返回了数据，但没有找到 [{target_contract}]。")
        print(f"ℹ️ 可用合约包括: {df['标的'].unique()}")
        return

    # 字段重命名 (API key -> Readable Name)
    col_map = {
        "dm": "Code",
        "p": "Price",
        "ccl": "OI",  # 持仓量
        "vol": "Vol",  # 成交量
        "xqj": "Strike",  # 行权价
        "yhbdl": "IV",  # 隐含波动率
        "delta": "Delta",
        "gamma": "Gamma",
        "vega": "Vega",
        "theta": "Theta",
        "rho": "Rho"
    }
    df_target = df_target.rename(columns=col_map)

    # 数值类型转换
    numeric_cols = ["Price", "Strike", "OI", "Vol", "IV", "Delta", "Gamma", "Vega", "Theta", "Rho"]
    for col in numeric_cols:
        if col in df_target.columns:
            df_target[col] = pd.to_numeric(df_target[col], errors='coerce')

    # 区分 Call 和 Put
    df_target['Type'] = df_target['Code'].apply(lambda x: 'Call' if 'C' in x.upper() else 'Put')

    # 4. 构建 T型报价 (Call放左边，Put放右边)
    # 定义需要的列
    metrics = ['Price', 'OI', 'Vol', 'IV', 'Delta', 'Gamma', 'Vega', 'Theta', 'Rho']
    # 确保这些列存在于df中
    valid_metrics = [m for m in metrics if m in df_target.columns]

    # 分割数据
    calls = df_target[df_target['Type'] == 'Call'][['Strike'] + valid_metrics].copy()
    puts = df_target[df_target['Type'] == 'Put'][['Strike'] + valid_metrics].copy()

    # 重命名列：Call 加 "购_", Put 加 "沽_" (或者用英文 Call_, Put_)
    calls.columns = ['Strike'] + [f"Call_{c}" for c in valid_metrics]
    puts.columns = ['Strike'] + [f"Put_{c}" for c in valid_metrics]

    # 合并 (Outer Join 保证单边报价也能显示)
    df_t = pd.merge(calls, puts, on='Strike', how='outer')
    df_t = df_t.sort_values('Strike').reset_index(drop=True)

    # 填充空值，方便查看
    df_final = df_t.fillna(0)

    # 5. 排列列顺序 (符合交易习惯)
    # 左侧: Delta -> IV -> Vol -> OI -> Price
    # 中间: Strike
    # 右侧: Price -> OI -> Vol -> IV -> Delta

    # 动态生成列列表，防止缺少字段报错
    left_side = [f"Call_{c}" for c in ['Delta', 'Gamma', 'Vega', 'Theta', 'Rho', 'IV', 'Vol', 'OI', 'Price']]
    right_side = [f"Put_{c}" for c in ['Price', 'OI', 'Vol', 'IV', 'Rho', 'Theta', 'Vega', 'Gamma', 'Delta']]

    left_exist = [c for c in left_side if c in df_final.columns]
    right_exist = [c for c in right_side if c in df_final.columns]

    final_cols = left_exist + ['Strike'] + right_exist
    df_final = df_final[final_cols]

    # --- 输出与保存 ---

    # 1. 打印预览
    print(f"\n📊 [{target_contract}] T型报价预览 (中间10档):")
    mid = len(df_final) // 2
    print(df_final.iloc[max(0, mid - 5): min(len(df_final), mid + 5)].to_markdown(index=False, floatfmt=".4f"))

    # 2. 保存到 CSV
    today_str = datetime.now().strftime("%Y%m%d")
    filename = f"{target_contract}_options_{today_str}.csv"

    print(f"\n💾 [3/4] 正在保存到本地文件...")
    try:
        # utf-8-sig 确保 Excel 打开中文不乱码
        df_final.to_csv(filename, index=False, encoding='utf-8-sig')

        abs_path = os.path.abspath(filename)
        print(f"✅ [4/4] 成功！文件已保存至:\n   👉 {abs_path}")
        print(f"   (共 {len(df_final)} 个行权价)")

    except Exception as e:
        print(f"❌ 保存文件失败 (可能文件被占用): {e}")


if __name__ == "__main__":
    # 支持的品种: ni(镍), ag(白银), au(黄金), sc(原油), lc(集运指数)
    # 示例: ni2603, ag2502, au2504, sc2503, lc2504
    fetch_and_save_options("ag2604")