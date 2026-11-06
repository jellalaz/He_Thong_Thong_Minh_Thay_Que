// Presentation preference is a hint; all routing and medical checks remain on the local backend.
const formatControls=document.createElement('div');
formatControls.className='chat-options';
formatControls.innerHTML='<label for="reply-format">Cách trả lời</label><select id="reply-format"><option value="auto">Tự chọn theo phản hồi</option><option value="brief">Ngắn gọn</option><option value="steps">Hướng dẫn từng bước</option><option value="explain">Giải thích kỹ</option></select>';
document.querySelector('#chat-form').prepend(formatControls);
const baseApi=api;
api=async function(url,body){
  if(url==='/api/chat'&&body)body={...body,preferred_format:document.querySelector('#reply-format').value};
  return baseApi(url,body);
};

// Escape first, then support a deliberately small set of formatting marks from local model text.
function formatAnswer(text){
  text=String(text).replace(/[^.!?\n]*(?:không (?:được )?(?:đề cập|nêu|có)|chưa (?:đề cập|có))[^.!?\n]*\[[a-zA-Z][a-zA-Z0-9_-]*\][^.!?\n]*[.!?]?/gi,'').replace(/\s*\[[a-zA-Z][a-zA-Z0-9_-]*\]/g,'').trim();
  return esc(text).replace(/\*\*([^*\n]+)\*\*/g,'<strong>$1</strong>');
}
const baseReply=addReply;
addReply=function(reply){
  baseReply(reply);
  const answers=document.querySelectorAll('.message:not(.user) .answer-text');
  if(answers.length)answers[answers.length-1].innerHTML=formatAnswer(reply.answer);
};
