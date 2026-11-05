"""Suy luận từ tham số thực nghiệm đã xuất; chỉ dùng Python standard library.

Được đóng gói nguyên vào API Vercel, không nạp torch/scikit-learn khi phục vụ.
"""
import math


def dot(a,b):return sum(x*y for x,y in zip(a,b))


def tree_predict(t,x):
    i=0
    while t['left'][i]!=-1:i=t['left'][i] if x[t['feature'][i]]<=t['threshold'][i] else t['right'][i]
    return t['value'][i]


def estimator_predict(m,x):
    typ=m['type']
    if typ=='pipeline':return estimator_predict(m['estimator'],[(v-mu)/s for v,mu,s in zip(x,m['mean'],m['scale'])])
    if typ=='constant':return m['value']
    if typ=='linear':return dot(m['coef'],x)+m['intercept']
    if typ=='forest':
        import struct
        x=[struct.unpack('f',struct.pack('f',v))[0] for v in x]
        return sum(tree_predict(t,x) for t in m['trees'])/len(m['trees'])
    if typ=='boost':return m['base']+m['rate']*sum(tree_predict(t,x) for t in m['trees'])
    if typ=='forest_classifier':
        votes=[0.]*len(m['classes'])
        # sklearn tree inference casts features to float32.
        import struct
        x=[struct.unpack('f',struct.pack('f',v))[0] for v in x]
        for t in m['trees']:
            v=tree_predict(t,x);s=sum(v)
            for i,z in enumerate(v):votes[i]+=z/s/len(m['trees'])
        return {'label':m['classes'][max(range(len(votes)),key=lambda i:votes[i])], 'scores':dict(zip(m['classes'],votes))}
    if typ=='logistic':
        logits=[dot(a,x)+b for a,b in zip(m['coef'],m['intercept'])]; mx=max(logits);ex=[math.exp(z-mx) for z in logits];sm=sum(ex)
        return {'label':m['classes'][logits.index(mx)],'scores':dict(zip(m['classes'],[v/sm for v in ex]))}
    raise ValueError('Estimator không hỗ trợ: '+typ)


def conv(image,weights,bias):
    channels=len(weights);height=len(image[0]);width=len(image[0][0]);out=[]
    for oc in range(channels):
        plane=[]
        for y in range(height):
            row=[]
            for x in range(width):
                s=bias[oc]
                for ic,kernel in enumerate(weights[oc]):
                    for ky in range(3):
                        yy=y+ky-1
                        if 0<=yy<height:
                            for kx in range(3):
                                xx=x+kx-1
                                if 0<=xx<width:s+=image[ic][yy][xx]*kernel[ky][kx]
                row.append(max(0.,s))
            plane.append(row)
        out.append(plane)
    return out


def pool(image):
    return [[[max(p[y][x],p[y+1][x],p[y][x+1],p[y+1][x+1]) for x in range(0,len(p[0]),2)] for y in range(0,len(p),2)] for p in image]


def cnn_predict(model,pixels):
    if not isinstance(pixels,list) or len(pixels)!=784:raise ValueError('Ảnh phải có 784 pixel (28 × 28).')
    if any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or not 0<=v<=255 for v in pixels):raise ValueError('Pixel phải nằm trong 0–255.')
    if not any(pixels):raise ValueError('Ảnh trống. Hãy vẽ chữ số hoặc chọn ảnh test.')
    w=model['weights'];image=[[pixels[i*28:(i+1)*28] for i in range(28)]]
    image=[[[v/255. for v in row] for row in image[0]]]
    z=pool(conv(image,w['conv1.weight'],w['conv1.bias']))
    z=pool(conv(z,w['conv2.weight'],w['conv2.bias']))
    flat=[v for p in z for row in p for v in row]
    h=[max(0.,dot(row,flat)+b) for row,b in zip(w['fc1.weight'],w['fc1.bias'])]
    logits=[dot(row,h)+b for row,b in zip(w['fc2.weight'],w['fc2.bias'])]
    exp=[math.exp(v-max(logits)) for v in logits];total=sum(exp)
    return {'digit':int(max(range(10),key=lambda i:logits[i])),'probabilities':[v/total for v in exp], 'logits':logits}


def sigmoid(x):return 1./(1.+math.exp(-max(-700.,min(700.,x))))


def sequence_predict(model,returns,last_close,kind=None):
    kind=kind or model['kind']
    if not isinstance(returns,list) or len(returns)!=30 or any(isinstance(x,bool) or not isinstance(x,(int,float)) or not math.isfinite(x) or abs(x)>1 for x in returns):raise ValueError('Cần đúng 30 log-return hữu hạn trong [-1, 1].')
    if not isinstance(last_close,(float,int)) or isinstance(last_close,bool) or not math.isfinite(last_close) or last_close<=0:raise ValueError('Giá đóng cửa phải là số dương hữu hạn.')
    if kind=='Persistence':return {'prediction':last_close,'predicted_log_return':0.,'model':'Persistence'}
    w=model['weights'];h=[0.]*16;c=[0.]*16
    wi=w['recurrent.weight_ih_l0'];wh=w['recurrent.weight_hh_l0'];bi=w['recurrent.bias_ih_l0'];bh=w['recurrent.bias_hh_l0']
    for r in returns:
        x=(r-model['mu'])/model['sigma'];ih=[row[0]*x+b for row,b in zip(wi,bi)];hh=[dot(row,h)+b for row,b in zip(wh,bh)]
        z=[a+b for a,b in zip(ih,hh)]
        if kind=='RNN':h=[math.tanh(v) for v in z]
        elif kind=='LSTM':
            i,f,g,o=[z[j*16:(j+1)*16] for j in range(4)]
            c=[sigmoid(fv)*cv+sigmoid(iv)*math.tanh(gv) for fv,cv,iv,gv in zip(f,c,i,g)]
            h=[sigmoid(ov)*math.tanh(cv) for ov,cv in zip(o,c)]
        elif kind=='GRU':
            reset=[sigmoid(v) for v in z[:16]];update=[sigmoid(v) for v in z[16:32]]
            cand=[math.tanh(a+r*b) for a,r,b in zip(ih[32:],reset,hh[32:])]
            h=[(1-u)*n+u*old for u,n,old in zip(update,cand,h)]
        else:raise ValueError('Kiểu mạng không hỗ trợ.')
    ret=(dot(w['head.weight'][0],h)+w['head.bias'][0])*model['yscale']+model['ym']
    return {'prediction':last_close*math.exp(ret),'predicted_log_return':ret,'model':kind}


def vectorize(model,features):
    if not isinstance(features,dict):raise ValueError('features phải là object.')
    x=[];warnings=[]
    for k,median,mu,scale in zip(model['numeric'],model['medians'],model['means'],model['scales']):
        value=features.get(k)
        if value is None or value=='':value=median;warnings.append(k+': dùng trung vị train')
        if isinstance(value,bool) or not isinstance(value,(float,int)) or not math.isfinite(value):raise ValueError(k+': cần số hữu hạn.')
        if value<=0:raise ValueError(k+': cần số dương.')
        if k in model.get('ranges',{}):
            lo,hi=model['ranges'][k]
            if value<lo or value>hi:warnings.append(k+': ngoài phạm vi train')
        x.append((value-mu)/scale)
    for k,categories in zip(model.get('categorical',[]),model.get('categories',[])):
        v=features.get(k,'Unknown')
        if not isinstance(v,str) or len(v)>150:raise ValueError(k+': chuỗi không hợp lệ.')
        if v not in categories:warnings.append(k+': nhóm chưa gặp trong train')
        x.extend(float(v==c) for c in categories)
    return x,warnings


def predict(bundle,payload):
    if not isinstance(payload,dict):raise ValueError('Yêu cầu JSON object.')
    kind=payload.get('task')
    if kind=='cnn':return cnn_predict(bundle['cnn'],payload.get('pixels'))
    if kind in ['housing','diabetes_classifier']:
        m=bundle[kind];x,warnings=vectorize(m,payload.get('features',{}));p=estimator_predict(m['estimator'],x)
        if kind=='housing':return {'prediction':math.expm1(p) if m.get('log_target') else p,'unit':'tỷ VND','warnings':warnings,'model':m['name']}
        return {**p,'warnings':warnings,'model':m['name'],'meaning':'Nhãn của dataset tổng hợp; không phải xác suất mắc bệnh.'}
    if kind=='sequence':
        domain=payload.get('domain','fpt')
        if domain not in bundle['sequences']:raise ValueError('domain phải là fpt hoặc gold.')
        m=bundle['sequences'][domain]
        return {**sequence_predict(m,payload.get('returns',m['last_returns']),payload.get('last_close',m['last_close'])),'unit':m['unit'],'as_of':m['as_of'],'neural_validation_winner':m['neural_validation_winner']}
    raise ValueError('task không hợp lệ.')
