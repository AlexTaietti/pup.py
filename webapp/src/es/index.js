const resultDisplay = document.getElementById("result")
const startButton = document.getElementById("start-button")

let currentStart = undefined
let currentTarget = undefined
let running = false
let resultFound = false


////////////////////
// action buttons //
////////////////////
const backTop = document.getElementById("back-top")
const clearAll = document.getElementById("clear-all")
const scrollLock = document.getElementById("scroll-lock")
const scrollLockInnerIcon = scrollLock.getElementsByTagName("i")[0]
const resultFlag = document.getElementById("flag")
const restart = document.getElementById("restart")
const abort = document.getElementById("stop")


const toggleLockScroll = () => {
	if (!scrollLock.classList.contains("enabled")) {
		scrollLockInnerIcon.classList.remove("fa-lock-open")
		scrollLockInnerIcon.classList.add("fa-lock")
		scrollLock.classList.add("enabled")
	} else {
		scrollLock.classList.remove("enabled")
		scrollLockInnerIcon.classList.remove("fa-lock")
		scrollLockInnerIcon.classList.add("fa-lock-open")
	}
}


const displayAlert = (message) => {

	const busy = document.getElementById("busy")
	const previoiusAlertText = busy.getElementsByClassName("alert-text") ? busy.getElementsByClassName("alert-text")[0] : null

	if (previoiusAlertText) busy.removeChild(previoiusAlertText)

	const alertText = document.createElement("p")
	alertText.classList.add("alert-text")
	alertText.textContent = message

	busy.appendChild(alertText)

	busy.classList.remove("hidden")
	setTimeout(() => busy.classList.add("hidden"), 5000)

}


const startNewRun = (start, target) => {

	clearAllUpdates()

	const formData = { "start": start, "target": target }
	socket.emit("fetch", { start, target })
	currentStart = start
	currentTarget = target
	running = true
	startButton.classList.add("running")
	startButton.value = "Running!"
	restart.classList.add("enabled")
	abort.classList.add("enabled")

}


const stopRun = () => {
	
	clearAllUpdates()
	
	socket.emit("stop")

	running = false
	startButton.classList.remove("running")
	startButton.value = "Let's go!"
	abort.classList.remove("enabled")

}


const clearAllUpdates = () => {

	if (resultDisplay.innerHTML) {
		resultDisplay.innerHTML = ""
		clearAll.classList.remove("enabled")
	}

	resultFound = false

	if (resultFlag.classList.contains("enabled")) resultFlag.classList.remove("enabled")

}


const createInfoItem = (data) => {

	const updateItem = document.createDocumentFragment()
	const currentArticle = document.createElement("a")

	const paragraphContainer = document.createElement("div")
	paragraphContainer.classList.add("best-paragraph")

	const similarity = document.createElement("p")
	similarity.classList.add("similarity")

	const header = document.createElement("p")
	header.classList.add("header")

	currentArticle.href = data["current_url"]
	currentArticle.textContent = data["current_url"].split("/").pop().split("_").toString().toLowerCase().split(",").join(" ")

	header.textContent = "From "
	header.appendChild(currentArticle)

	paragraphContainer.innerHTML = data["paragraph"]
	similarity.textContent = `This paragraph's similarity score is ~${data["similarity"]}`

	updateItem.appendChild(header)
	updateItem.appendChild(paragraphContainer)
	updateItem.appendChild(similarity)

	return updateItem

}


const showUpdate = (update) => {

	const updateObject = update["update"]
	const updateItem = document.createElement("li")
	updateItem.classList.add("update-container")

	const fragment = createInfoItem(updateObject["data"])
	updateItem.classList.add("info")
	updateItem.appendChild(fragment)

	if (!resultDisplay.innerHTML) clearAll.classList.add("enabled")

	if (updateObject["type"] == "SUCCESS") {

		resultFound = true
	
		updateItem.classList.add("success")

		resultFlag.onclick = () => updateItem.scrollIntoView({ behavior: "smooth" })

		if (!scrollLock.classList.contains("enabled")) {
			if (!resultFlag.classList.contains("enabled")) resultFlag.classList.add("enabled")
		}

		running = false
		startButton.classList.remove("running")
		startButton.value = "Let's go!"
		abort.classList.remove("enabled")

	}

	resultDisplay.appendChild(updateItem)

	if (scrollLock.classList.contains("enabled")) updateItem.scrollIntoView({ behavior: "smooth" })

}


const submitForm = () => {

	const start = document.getElementById("start").value
	const target = document.getElementById("target").value

	if(!start || !target){
		displayAlert("We are missing either one of the two inputs")
		return
	}

	if (!start.includes("en.wikipedia.org") || !target.includes("en.wikipedia.org")) {
		displayAlert("Invalid input, make sure the links supplied come from en.wikipedia.com")
		return
	}

	startNewRun(start, target)

}


const scrollToTop = () => window.scrollTo({ top: 0, behavior: 'smooth' })


restart.addEventListener("click", () => startNewRun(currentStart, currentTarget))
backTop.addEventListener("click", scrollToTop)
clearAll.addEventListener("click", clearAllUpdates)
scrollLock.addEventListener("click", toggleLockScroll)
abort.addEventListener("click", stopRun)


/////////////////////
// websocket stuff //
/////////////////////
const socketServerIP = location.hostname === "localhost" ? "127.0.0.1" : location.hostname
const socket = io.connect(`http://${socketServerIP}:5000`)

socket.on('connected', (message) => console.log('socketIO connected', message))

socket.on('puppy live update', showUpdate)

socket.on('all puppers busy', displayAlert)


////////////////////
// windows events //
////////////////////
window.addEventListener("scroll", () => {

	if (window.scrollY && !backTop.classList.contains("enabled")) {
		backTop.classList.add("enabled")
	}

	if (!window.scrollY && backTop.classList.contains("enabled")) {
		backTop.classList.remove("enabled")
	}

	if (resultFound) {
		if ((window.innerHeight + window.scrollY) >= document.body.scrollHeight) {
			resultFlag.classList.remove("enabled")
		} else if (!resultFlag.classList.contains("enabled")) {
			resultFlag.classList.add("enabled")
		}
	}

})


window.addEventListener("beforeunload", () => socket.emit("disconnect"))
