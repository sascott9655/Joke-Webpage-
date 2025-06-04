// Admin control to delete jokes from the homepage
function deleteJoke(event){
    const confirmed = confirm("Are you sure you want to delete this joke?")
        if(!confirmed){
            event.preventDefault(); //prevent form from submitting
        }
}

document.addEventListener('DOMContentLoaded', function(){
    const deleteButtons = document.querySelectorAll('#delete-button');
    deleteButtons.forEach(function (button){
        button.addEventListener('click', deleteJoke);
    });     
});




// Admin approving jokes to exist on the website 
// function approveJoke(jokeId) {
//     fetch(`/approve/${jokeId}`, {method: 'POST'})
//         .then(function() {
//             document.getElementById(`joke-${jokeId}`).remove();
//         }); 
// }
// function rejectJoke(jokeId) {
//     fetch(`/reject/${jokeId}`, {method: 'POST'})
//         .then(function() {
//             document.getElementById(`joke-${jokeId}`).remove();
//         }); 
// }




// Comments button toggling when we view jokes and user accounts
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


// sets a timer of displaying flash-messages
setTimeout(() => {
    const flashContainer = document.querySelector('.flash-messages');
    if(flashContainer) {
        flashContainer.style.display = 'none';
    }
}, 5000);