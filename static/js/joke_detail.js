function toggleComments(){
   const commentSection = document.querySelector('.comment-section-wrapper');
   const button = document.querySelector('.comment-section-button')
   if(commentSection.style.display === 'none' || commentSection.style.display === ''){
       commentSection.style.display = 'block'; 
       button.textContent = "Hide Comments ↑";
   } else {
        commentSection.style.display = 'none'; 
        button.textContent = "Show Comments ↓";
   }
}

document.addEventListener('DOMContentLoaded', function() {
    const button = document.querySelector('.comment-section-button');
    button.addEventListener('click', toggleComments);
})
