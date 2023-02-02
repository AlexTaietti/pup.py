const resultDisplay = document.getElementById("result") 
const socket = io.connect('http://127.0.0.1:5000')

const createInfoFragment = (data) => {
	
	const DOMFragment = document.createDocumentFragment()
	const currentArticle = document.createElement("a")
	const nextArticle = document.createElement("a")
	const paragraph = document.createElement("p")
	const info = document.createElement("p")

	currentArticle.href = currentArticle.textContent = data["current_url"]
	nextArticle.href = nextArticle.textContent = data["best_link"]

	paragraph.textContent = data["paragraph"]
	paragraph.classList.add("best-paragraph")

	const linksNumber = document.createTextNode(data["links_n"])
	const similarity = document.createTextNode(data["similarity"])

	info.appendChild(linksNumber)
	info.appendChild(similarity)
	info.appendChild(currentArticle)
	info.appendChild(nextArticle)

	DOMFragment.appendChild(paragraph)
	DOMFragment.appendChild(info)

	return DOMFragment

}

const showUpdate = (update) => {

	const updateObject = update["update"]
	
	let DOMFragment

	if (updateObject["type"] == "INFO"){
		DOMFragment = createInfoFragment(updateObject["data"])
	} else {
		console.log(updateObject["data"])
	}

	const updateElement = document.createElement("li")
	updateElement.classList.add("update-entry")
	updateElement.append(DOMFragment)
        resultDisplay.appendChild(updateElement)

}

const submitForm = () => {

	const start = document.getElementById("start").value
	const target = document.getElementById("target").value
	
	if (!start || !target) return

	if (resultDisplay.innerHTML) { resultDisplay.innerHTML = "" }

	const formData = { "start": start, "target": target }
	const startMessage = `Asking puppy to find the path from ${start} to ${target}`

	socket.emit("fetch", { start, target })

}

socket.on('found', (message) => console.log(message))

socket.on('busy', (message) => console.log(message))

socket.on('connected', (message) => console.log('socketIO connected', message))

socket.on('puppy live update', showUpdate)
