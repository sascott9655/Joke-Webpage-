function deleteJoke(){
    const confirmed = confirm("Are you sure you want to delete this joke?")
        if(!confirmed){
            event.preventDefault(); //prevent form from submitting
        }
}

document.addEventListener('DOMContentLoaded', function(){
    const deleteButtons = document.querySelectorAll('.delete-button');
    deleteButtons.forEach(function (button){
        button.addEventListener('click', deleteJoke);
    });
});

function toggleComments(id){
    const commentsDiv = document.getElementById(id);
    if(commentsDiv.style.display === "none") {
        commentsDiv.style.display = "block";
    } else {
        commentsDiv.style.display = "none";
    }
}

document.addEventListener('DOMContentLoaded', function(){
    commentButton.forEach(function(button){
        const jokeId = button.getAttribute('data-joke-id');
        const commentDivId = `comments-${jokeId}`;
        button.addEventListener('click', function(){
            toggleComments(commentDivId);
        });
    })
});
