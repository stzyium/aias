const weburl = "ws://localhost:5000";
const socket = new WebSocket(weburl);
const cheit = document.querySelector('.container').clientHeight;
const imc = document.getElementById('imagecontainer');

imc.style.height = `${cheit-4}px`;
socket.onopen = () => {
  setNotification('Connected to the server... Awaiting Action...');
}
socket.onerror = (error) => {
console.error("socket error:", error);
}
function clearInput(id) {
  document.getElementById(id).value = '';
  setNotification(`Cleared input for ${id}!`);
}

function lock(what) {
  const name = document.getElementById('name');
  const roll = document.getElementById('roll');
  const grade = document.getElementById('grade');
  const section = document.getElementById('section');
  const iname = document.getElementById('iname');
  const iroll = document.getElementById('iroll');
  const igrade = document.getElementById('igrade');
  const isection = document.getElementById('isection');

  if (what === 'name') {
    name.disabled = true;
    iname.className = 'fa fa-lock'
  } else if (what === 'roll') {
    roll.disabled = true;
    iroll.className = 'fa fa-lock'
  }

}

function trackImage() {
  const ar = {
    type: "track"
  };
  const json = JSON.stringify(ar);
  if (socket.readyState === WebSocket.OPEN) {
    socket.send(json);
    openCamera('track');
  } else {
    console.error(socket.readyState);
  }
}
function trainImage() {
  ar = {
    type: 'train'
  };
  const json = JSON.stringify(ar);
  
  if (socket.readyState === WebSocket.OPEN) {
    socket.send(json);
    setNotification("Training request sent.");
  } else {
    console.error("WebSocket is not open. Current state:", socket.readyState);
  }
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
    if (Number.isInteger(n) || !isNaN(n)) {
      alertNotification('Roll Number should be an integer.')
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

function openCamera(type) {
  const cameraElement = document.getElementById('camera');
  const sideCamera = document.getElementById('sidecamera');
  if (type==='track') {
    sideCamera.hidden = true;
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
