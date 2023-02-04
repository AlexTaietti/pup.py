const resultDisplay = document.getElementById("result") 
const socket = io.connect('http://127.0.0.1:5000')

const createInfoItem = (data) => {
	
	const updateItem = document.createDocumentFragment()
	
	const currentArticle = document.createElement("a")
	
	const paragraph = document.createElement("p")
	paragraph.classList.add("best-paragraph")
	
	const similarity = document.createElement("p")
	similarity.classList.add("similarity")
	
	const header = document.createElement("p")
	header.classList.add("header")

	currentArticle.href = data["current_url"]
	currentArticle.textContent = data["current_url"].split("/").pop().split("_").toString().toLowerCase().split(",").join(" ")

	header.textContent = "From "
	header.appendChild(currentArticle)

	paragraph.textContent = `“${data["paragraph"]}”`
	similarity.textContent = `This paragraph's similarity score is ~${data["similarity"]}`

	updateItem.appendChild(header)
	updateItem.appendChild(paragraph)
	updateItem.appendChild(similarity)

	return updateItem

}

const createLoopItem = (data) => {

	const DOMFragment = document.createDocumentFragment()

	const exclamation = document.createElement("span")
	exclamation.textContent = "!"
	const text = document.createElement("p")
	text.textContent = "Oh no! Puppy got stuck in a loop here "
	const stuckPageLink = document.createElement("a")
	stuckPageLink.href = data["current_url"]
	stuckPageLink.textContent = data["current_url"].split("/").pop().split("_").toString().toLowerCase().split(",").join(" ")
	text.appendChild(stuckPageLink)
	const moreText = document.createTextNode(", going back to the starting page...")
	text.appendChild(moreText)

	DOMFragment.appendChild(exclamation)
	DOMFragment.appendChild(text)

	return DOMFragment

}

const showUpdate = (update) => {

	const updateObject = update["update"]
	const updateItem = document.createElement("li")
        updateItem.classList.add("update-container")

	if (updateObject["type"] == "INFO"){
		const fragment = createInfoItem(updateObject["data"])
		updateItem.classList.add("info")
		updateItem.appendChild(fragment)
	} else if (updateObject["type"] == "LOOP") {
		const fragment = createLoopItem(updateObject["data"])
		updateItem.classList.add("loop")
                updateItem.appendChild(fragment)
	} else {
		console.log(updateObject["data"])
		return
	}

        resultDisplay.appendChild(updateItem)

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
