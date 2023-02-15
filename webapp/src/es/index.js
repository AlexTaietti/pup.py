const resultDisplay = document.getElementById("result")


////////////////////
// action buttons //
////////////////////
const backTop = document.getElementById("back-top")
const clearAll = document.getElementById("clear-all")
const scrollLock = document.getElementById("scroll-lock")
const scrollLockInnerIcon = scrollLock.getElementsByTagName("i")[0]
const resultFlag = document.getElementById("flag")

// scroll locking
const toggleLockScroll = () => {
	if(!scrollLock.classList.contains("enabled")){
		scrollLockInnerIcon.classList.remove("fa-lock-open")
		scrollLockInnerIcon.classList.add("fa-lock")
		scrollLock.classList.add("enabled")
	} else {
		scrollLock.classList.remove("enabled")
		scrollLockInnerIcon.classList.remove("fa-lock")
                scrollLockInnerIcon.classList.add("fa-lock-open")
	}
}

// used to toggle flag button state
let resultFound = false

// update clearance
const clearAllUpdates = () => {
	
	if (resultDisplay.innerHTML) {
		resultDisplay.innerHTML = ""
		clearAll.classList.remove("enabled")
	}
	
	resultFound = false
	
	if (resultFlag.classList.contains("enabled")) resultFlag.classList.remove("enabled")

}

// scroll back to top
const scrollToTop = () => window.scrollTo({ top: 0, behavior: 'smooth' })



backTop.addEventListener("click", scrollToTop)
clearAll.addEventListener("click", clearAllUpdates)
scrollLock.addEventListener("click", toggleLockScroll)

/////////////////////
// websocket stuff //
/////////////////////
const socketServerIP = location.hostname === "localhost" ? "127.0.0.1" : location.hostname
const socket = io.connect(`http://${socketServerIP}:5000`)

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

	const paragraphContent = data["paragraph"].split("***").join("b")

	paragraph.innerHTML = `“${paragraphContent}”`
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
		const fragment = createInfoItem(updateObject["data"])
                updateItem.classList.add("info")
		updateItem.classList.add("success")
                updateItem.appendChild(fragment)
	}

	if (!resultDisplay.innerHTML){ clearAll.classList.add("enabled") }

        resultDisplay.appendChild(updateItem)

	if (updateObject["type"] == "SUCCESS") {
		
		resultFound = true
		resultFlag.onclick = () => updateItem.scrollIntoView({behavior: "smooth"})

		if (scrollLock.classList.contains("enabled")){
			updateItem.scrollIntoView({behavior: "smooth"})
		} else {
			if (!resultFlag.classList.contains("enabled")) resultFlag.classList.add("enabled")
		}
       	
	} else {

		if (scrollLock.classList.contains("enabled")) updateItem.scrollIntoView({behavior: "smooth"})

	}

}

const submitForm = () => {

	const start = document.getElementById("start").value
	const target = document.getElementById("target").value
	
	if (!start || !target) return

	clearAllUpdates()

	const formData = { "start": start, "target": target }
	const startMessage = `Asking puppy to find the path from ${start} to ${target}`

	socket.emit("fetch", { start, target })

}

window.addEventListener("scroll", () => {

	if(window.scrollY && !backTop.classList.contains("enabled")){
		backTop.classList.add("enabled")
  	}

	if (!window.scrollY && backTop.classList.contains("enabled")){
		backTop.classList.remove("enabled")
	}

	if (resultFound){
		if ((window.innerHeight + window.scrollY) >= document.body.scrollHeight) {
			resultFlag.classList.remove("enabled")
		} else if (!resultFlag.classList.contains("enabled")) {
			resultFlag.classList.add("enabled")
		}
	}

})

socket.on('connected', (message) => console.log('socketIO connected', message))

socket.on('puppy live update', showUpdate)
