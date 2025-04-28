function approveJoke(jokeId) {
    fetch(`/approve/${jokeId}`, {method: 'POST'})
        .then(function() {
            document.getElementById(`joke-${jokeId}`).remove();
        }); 
}
function rejectJoke(jokeId) {
    fetch(`/reject/${jokeId}`, {method: 'POST'})
        .then(function() {
            document.getElementById(`joke-${jokeId}`).remove();
        }); 
}