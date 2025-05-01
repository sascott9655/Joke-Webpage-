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