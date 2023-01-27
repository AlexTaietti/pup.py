const resultDisplay = document.getElementById("result"); 

const submitForm = () => {
	
	const formData = {
		"start": document.getElementById("start").value,
		"target": document.getElementById("target").value
	};
	
	fetch('http://127.0.0.1:5000/fetch', {
	  method: 'POST', 
	  headers: { 'Content-Type': 'application/json'},
	  body: JSON.stringify(formData)
	})
	.then(response => response.json())
	.then(data => {
		console.log('Success:', data);
		resultDisplay.innerHTML = data["result"];
	})
	.catch((error) => console.error('Error:', error));
}

// sending a connect request to the server.
const socket = io.connect('http://127.0.0.1:5000');

socket.on('connected', function(msg) { console.log('socketIO connected', msg); });
