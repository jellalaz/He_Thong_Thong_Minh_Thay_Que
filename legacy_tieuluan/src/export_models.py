# Xuất mô hình đã fit; JavaScript đọc cùng cấu trúc tham số/cây với Python.
def export_estimator(model):
    if isinstance(model, ReturnForecaster):
        return {"type":"return", "shrinkage":model.shrinkage, "estimator":export_estimator(model.estimator_)}
    if isinstance(model, PersistenceRegressor):
        return {"type":"persistence"}
    if isinstance(model, Pipeline):
        scaler = model.named_steps["scale"]
        return {"type":"pipeline", "mean":scaler.mean_.tolist(),"scale":scaler.scale_.tolist(),
                "estimator":export_estimator(model.named_steps["model"])}
    if isinstance(model,SVR):
        return {"type":"svr","support_vectors":model.support_vectors_.tolist(),
                "dual_coef":model.dual_coef_[0].tolist(),"gamma":float(model._gamma),
                "intercept":float(model.intercept_[0])}
    if hasattr(model,"coef_"):
        return {"type":"linear","coef":np.asarray(model.coef_).tolist(),"intercept":float(model.intercept_)}
    if isinstance(model,DummyRegressor):
        return {"type":"constant","value":float(model.constant_.ravel()[0])}
    def tree(t):
        a=t.tree_
        return {"left":a.children_left.tolist(),"right":a.children_right.tolist(),
                "feature":a.feature.tolist(),"threshold":a.threshold.tolist(),"value":a.value[:,0,0].tolist()}
    if isinstance(model,RandomForestRegressor):
        return {"type":"forest","trees":[tree(t) for t in model.estimators_]}
    if isinstance(model,GradientBoostingRegressor):
        return {"type":"boost","base":float(model.init_.constant_.ravel()[0]),
                "rate":model.learning_rate,"trees":[tree(t) for t in model.estimators_.ravel()]}
    raise TypeError(type(model).__name__)

def feature_stats(frame):
    return {k:{"min":float(frame[k].min()),"max":float(frame[k].max()),
               "value":float(frame[k].median())} for k in frame.columns}

web_config = {"version":"2.2","generated_at":RUN_AT.isoformat(),"student":{"name":STUDENT_NAME,"id":STUDENT_ID},"models":{}}
web_config["models"]["diabetes"] = {
    "estimator":export_estimator(diabetes_model),"features":list(X.columns),"name":diabetes_model_name,
    "metrics":diabetes_metrics,"inputs":feature_stats(X_train),"interval":diabetes_interval,
    "unit":"điểm tiến triển sau 1 năm","source":"scikit-learn · 442 quan sát đã mắc tiểu đường",
    "reference":{"q25":float(y_train.quantile(.25)),"median":float(y_train.median()),"q75":float(y_train.quantile(.75))},
    "comparison":diabetes_cv_rows,"importance":feature_importance.to_dict(),
    "evaluation":[{"actual":float(a),"prediction":float(p)} for a,p in zip(y_test,diabetes_pred)],
}
for key,label,df,model,metrics,features,latest,preds,rows in [
    ("stock","Chứng khoán FPT",stock_df,stock_model,stock_model_info,market_feature_cols,stock_latest_features,stock_predictions,stock_cv_rows),
    ("gold","Giá vàng GC=F",gold_df,gold_model,gold_model_info,gold_feature_cols,gold_latest_features,gold_predictions,gold_cv_rows)]:
    detail=market_details[label]
    effective_train=detail["train"].iloc[-model.window:] if isinstance(model,ReturnForecaster) and model.window else detail["train"]
    web_config["models"][key]={
        "estimator":export_estimator(model),"features":features,"name":metrics["Model"],"metrics":metrics,
        "inputs":feature_stats(detail["train"]),"latest":{k:float(v) for k,v in latest.items()},
        "interval":detail["live_interval"],"evaluation_interval":detail["interval"],
        "deployment":detail["deployment"],"comparison":rows,"source":market_sources[key],
        "currency":"VND" if key=="stock" else "USD/oz","symbol":"FPT.VN" if key=="stock" else "GC=F",
        "as_of":str(latest.name.date()),
        "ood_space":"relative" if isinstance(model,(ReturnForecaster,PersistenceRegressor)) else "raw",
        "ood_inputs":feature_stats(pd.DataFrame(ReturnForecaster.transform(effective_train),columns=features)) if isinstance(model,(ReturnForecaster,PersistenceRegressor)) else feature_stats(effective_train),
        "history":[{"date":str(i.date()),"close":float(r.Close),"ma20":float(r.MA20)} for i,r in df.dropna().tail(80).iterrows()],
        "evaluation":[{"date":str(i.date()),"actual":float(r.Actual),"prediction":float(r.Prediction),"baseline":float(r.Persistence)} for i,r in preds.iterrows()],
    }
# Mốc trước nâng cấp, cùng nhãn và cùng giai đoạn test; không dùng để tuning.
for key,old_mae,old_name in [("diabetes",42.9364023293,"Ridge"),("stock",728.1284466911765,"Persistence"),("gold",50.47005460824505,"Ridge return")]:
    web_config["models"][key]["previous"]={"version":"2.0","name":old_name,"mae":old_mae,
        "improvement_pct":100*(1-web_config["models"][key]["metrics"]["MAE"]/old_mae)}
# Vectors độc lập để kiểm tra sai số suy luận Python/JavaScript sau khi đóng gói.
parity_vectors=[]
for key,model,frame in [("diabetes",diabetes_model,X_test),("stock",stock_model,market_details["Chứng khoán FPT"]["test"]),("gold",gold_model,market_details["Giá vàng GC=F"]["test"])]:
    for _,row in frame.iloc[:12].iterrows():
        parity_vectors.append({"kind":key,"x":row.tolist(),"expected":float(model.predict(row.to_frame().T)[0])})
(DATA_DIR/"model_parity.json").write_text(json.dumps(parity_vectors),encoding="utf-8")
(DATA_DIR/"web_model_config.json").write_text(json.dumps(web_config,ensure_ascii=False,allow_nan=False),encoding="utf-8")
