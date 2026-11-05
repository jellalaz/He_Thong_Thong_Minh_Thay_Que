# Dữ liệu thật; nếu mất mạng chỉ đọc snapshot đã lưu, không thay bằng giá mô phỏng.
def yahoo_chart(symbol, range_="5y", interval="1d"):
    url=f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
    response=requests.get(url,params={"range":range_,"interval":interval,"events":"history"},
                          timeout=25,headers={"User-Agent":"Mozilla/5.0"})
    response.raise_for_status()
    result=response.json()["chart"]["result"][0]
    frame=pd.DataFrame(result["indicators"]["quote"][0],
                       index=pd.to_datetime(result["timestamp"],unit="s",utc=True).tz_convert(None))
    frame.index.name="Date"
    frame.columns=[c.title() for c in frame.columns]
    frame=frame[["Open","High","Low","Close","Volume"]].sort_index()
    frame=frame[~frame.index.duplicated(keep="last")].dropna()
    frame=frame[(frame.Close>0)&(frame.Open>0)&(frame.High>=frame.Low)&(frame.Volume>=0)]
    # Không dùng phiên chưa kết thúc: cửa sổ 24h bảo thủ cho cả hai sàn.
    frame=frame[frame.index < pd.Timestamp.now(tz="UTC").tz_localize(None)-pd.Timedelta(hours=24)]
    if len(frame)<200: raise ValueError("Nguồn trả về quá ít quan sát hợp lệ")
    return frame,result.get("meta",{})

def add_indicators(df):
    out=df.copy().sort_index()
    out["Return_1D"]=out.Close.pct_change(fill_method=None)
    out["MA20"]=out.Close.rolling(20).mean()
    out["MA60"]=out.Close.rolling(60).mean()
    out["Volatility20"]=out.Return_1D.rolling(20).std()*np.sqrt(252)
    delta=out.Close.diff();gain=delta.clip(lower=0).rolling(14).mean();loss=(-delta.clip(upper=0)).rolling(14).mean()
    out["RSI14"]=100-100/(1+gain/loss.replace(0,np.nan))
    out.loc[(loss==0)&(gain>0),"RSI14"]=100
    out.loc[(loss==0)&(gain==0),"RSI14"]=50
    return out

diabetes=load_diabetes(as_frame=True,scaled=False)
diabetes_df=diabetes.frame.copy();diabetes_df.index.name="Patient_Row"
diabetes_df.to_csv(DATA_DIR/"diabetes_processed.csv")
market_sources={}
market_data={}
for key,symbol,filename,currency in [("stock","FPT.VN","fpt_stock_processed.csv","VND"),("gold","GC=F","gold_futures_processed.csv","USD")]:
    try:
        raw,meta=yahoo_chart(symbol)
        market_sources[key]="Yahoo Finance chart API - "+symbol
    except Exception as exc:
        cached=DATA_DIR/filename
        if not cached.exists():
            raise RuntimeError(f"Không tải được {symbol} và chưa có snapshot. Hãy kiểm tra mạng và chạy lại.") from exc
        raw=pd.read_csv(cached,index_col=0,parse_dates=True)[["Open","High","Low","Close","Volume"]].dropna()
        raw=raw[raw.index<pd.Timestamp.now(tz="UTC").tz_localize(None)-pd.Timedelta(hours=24)]
        meta={"currency":currency,"symbol":symbol}
        market_sources[key]="Yahoo snapshot lưu trước - "+symbol
        print(f"{symbol}: dùng snapshot đến {raw.index.max().date()} do {type(exc).__name__}.")
    df=add_indicators(raw)
    df.to_csv(DATA_DIR/filename)
    market_data[key]=(raw,meta,df)
stock_raw,stock_meta,stock_df=market_data["stock"]
gold_raw,gold_meta,gold_df=market_data["gold"]
print("Diabetes:",len(diabetes_df),"| FPT:",len(stock_df),"| Gold:",len(gold_df))
print(market_sources)
