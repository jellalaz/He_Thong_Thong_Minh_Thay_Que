// Carry an explicitly selected research form into follow-up turns; never infer a diagnosis.
let activeResearchContext = null;
const contextNote = document.createElement('div');
contextNote.id = 'research-context-note';
contextNote.hidden = true;
contextNote.className = 'context-label';
contextNote.innerHTML = '<span>Đang trao đổi từ mẫu nghiên cứu; kết quả không xác lập chẩn đoán.</span> <button type="button" class="text-button">Bỏ ngữ cảnh mẫu</button>';
document.querySelector('#chat-form').before(contextNote);
function clearResearchContext(){activeResearchContext=null;contextNote.hidden=true;}
contextNote.querySelector('button').onclick=clearResearchContext;
const researchBaseSend=sendQuestion;
sendQuestion=async function(question,modelContext=null){
  if(busy)return;
  if(modelContext?.task&&modelContext?.values){
    activeResearchContext={task:modelContext.task,values:{...modelContext.values}};
    contextNote.hidden=false;
  }
  return researchBaseSend(question,modelContext);
};
const researchBaseApi=api;
api=async function(url,body){
  if(url==='/api/chat'&&body&&(body.task||'knowledge')==='knowledge'&&activeResearchContext){
    body={...body,model_context:activeResearchContext};
  }
  return researchBaseApi(url,body);
};
const researchNewChat=document.querySelector('#new-chat').onclick;
document.querySelector('#new-chat').onclick=()=>{clearResearchContext();researchNewChat();};
