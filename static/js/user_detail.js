function toggleComments(){
   const button = event.currentTarget;
   const jokeContainer = button.closest('.joke');
   const commentSection = jokeContainer.querySelector('.comment-section-wrapper');
//    const button = document.querySelector('.comment-section-button')
   
   if(commentSection.style.display === 'none' || commentSection.style.display === ''){
       commentSection.style.display = 'block'; 
       button.textContent = "Hide Comments ↑";
   } else {
        commentSection.style.display = 'none'; 
        button.textContent = "Show Comments ↓";
   }
}

document.addEventListener('DOMContentLoaded', function() {
    const button = document.querySelectorAll('.comment-section-button');
    button.forEach(function (button){
        button.addEventListener('click', toggleComments);
    });
})
