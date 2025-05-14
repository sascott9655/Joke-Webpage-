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

function toggleComments(id, button){
    const commentsDiv = document.getElementById(id);
    if(commentsDiv.style.display === "none") {
        commentsDiv.style.display = "block";
        button.textContent = "Hide Comments";
    } else {
        commentsDiv.style.display = "none";
        button.textContent = "Show Comments";
    }
}

document.addEventListener('DOMContentLoaded', function(){
    const commentButton = document.querySelectorAll('.toggle-comments');
    commentButton.forEach(function(button){
        const jokeId = button.getAttribute('data-joke-id');
        const commentDivId = `comments-${jokeId}`;

        // Set initial text
        button.textContent = "Show Comments";

        button.addEventListener('click', function(){
            toggleComments(commentDivId, button);
        });
    })
});
