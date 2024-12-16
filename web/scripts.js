const weburl = "ws://localhost:5000";
const socket = new WebSocket(weburl);
const cheit = document.querySelector('.container').clientHeight;
const imc = document.getElementById('imagecontainer');
let reconnectAttempts = 0;
const maxReconnectAttempts = 10;
const reconnectDelay = 1000; 
imc.style.height = `${cheit-4}px`;
socket.onopen = () => {
  setNotification('Connected to the server... Awaiting Action...');
}
socket.onerror = (error) => {
console.error("socket error:", error);
}
socket.onclose = () => {
  setNotification("Websocket connection closed unexpectedly. Reconnecting...")
  attemptReconnect();
}
function clearInput(id) {
  document.getElementById(id).value = '';
  setNotification(`Cleared input for ${id}!`);
}
function attemptReconnect() {
  if (reconnectAttempts < maxReconnectAttempts) {
    reconnectAttempts++;
    const delay = reconnectDelay * reconnectAttempts; // Optional exponential backoff
    console.log(`Attempting to reconnect in ${delay / 1000} seconds...`);

    setTimeout(() => {
      console.log(`Reconnecting (attempt ${reconnectAttempts})...`);
      connectWebSocket();
    }, delay);
  } else {
    console.error('Max reconnect attempts reached. Stopping reconnection.');
  }
}

function cap() {
  window.location.href = "/dash";
}

function trackImage() {
  const ar = { type: "track" };
  const json = JSON.stringify(ar);

  if (socket.readyState === WebSocket.OPEN) {
    socket.send(json);
    openCamera('track');

    const button = document.getElementById('track');
    button.innerHTML = '<i class="fas fa-stop"></i> STOP';
    button.id = 'stop';
    
    button.onclick = () => {
      fetch('/api/stoptracking')
        .then(res => {
          if (res.ok) {
            setNotification('Stopped tracking...');
            const doc = document.getElementById('camera');
            doc.src = '/kvs';
            resetButton(button)
          } else {
            setNotification('Error stopping tracking.');
          }
        })
        .catch(err => setNotification('Error: ' + err.message));
    };
  } else {
    console.error('WebSocket is not open. Current state:', socket.readyState);
  }
}

function resetButton(button) {
  button.id = 'track';
  button.innerHTML = '<i class="fas fa-search"></i> TRACK';
  button.onclick = trackImage;
  
}

function trainImage() {
  setNotification("Training request sent...")
  fetch('/api/trainmodel')
  .then(response => response.text())
  .then(data => {
    setNotification(data);
  })
  .catch(error => console.log(error))
}

function captureImage() {
  const dname = document.getElementById('name').value.trim();
  const droll = document.getElementById('roll').value.trim();
  const dgrade = document.getElementById('grade').value.trim();
  const dsection = document.getElementById('section').value.trim();
  
  if (!dname || !droll || !dgrade || !dsection) {
    alertNotification("Please fill in all fields.");
    return;
  } else {
    if (!(Number.isInteger(droll) || !isNaN(droll))) {
      alertNotification('Roll Number should be an integer.')
      return;
    }
    const ar = {
      type: 'capture',
      name: dname,
      roll: droll,
      class: dgrade,
      section: dsection
    };
    console.log(ar);

    const json = JSON.stringify(ar);
    
    if (socket.readyState === WebSocket.OPEN) {
      socket.send(json);
    } else {
      console.error("WebSocket is not open. Current state:", socket.readyState);
      alertNotification("WebSocket is not open. Please try again.");
    }
    openCamera('capture');
  }
}

function alertNotification(message) {
  const notification = document.getElementById('notification');
  notification.style.color = '#ff0000';
  notification.textContent = message;

  console.log("Notification:", message);
}
function setNotification(message) {
  const notification = document.getElementById('notification');
  notification.style.color = '#ffffff';
  notification.textContent = message;
}

function openCamera(type, buts) {
  setNotification("Connecting to Camera...")
  const cameraElement = document.getElementById('camera');
  const sideCamera = document.getElementById('sidecamera');
  if (type==='track') {
    sideCamera.hidden = true;
  } else {
    sideCamera.hidden = false;
  }
  socket.onmessage = (event) => {
    try {
      const jsondata = JSON.parse(event.data)
      if (type === 'capture') {
          cameraElement.src = `data:image/jpeg;base64,${jsondata.camera}`;
          sideCamera.src = `data:image/jpeg;base64,${jsondata.sidecamera}`;
          setNotification(jsondata.text);
      } else {
          cameraElement.src = `data:image/jpeg;base64,${jsondata.camera}`;
          setNotification(jsondata.text);
      }
    } catch (error) {}
  };
}
