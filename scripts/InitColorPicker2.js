var secret = ""
// const SERVER = 'https://iot-dod-2021.rtuitlab.dev';
const SERVER = '';
this.socket = io(SERVER, {
  path: '/case/2/ws/socket.io',
  transports: ["websocket"]
});

// Socket events
this.socket.on('connect', () => {
  // console.log('Connected!');
  this.socket.emit('update_status', {
    presence: 'online',
    secret: this.secret,
    qr_secret_html: document.URL.split("=")[1]
  });
});

// handle the event sent with socket.send()
socket.on("message", data => {
  // console.log(data);
});

socket.on("new_token", data => {
  if (secret == "") {
    secret = data['secret']
    // // console.log(secret);
  }
});

socket.on("topic_data", data => {
  // console.log("" + data['topic'] + " " + data["msg"]);
  if (data['topic'] != "/devices/wb-mrgbw-d_78/controls/RGB") {
    item = document.getElementById(data['topic']).innerText = data["msg"];
  }
});

socket.on("timer", data => {
  // // console.log(data['secret']);
  // // console.log(secret);
  if (data['secret'] == secret) {
    document.body.style.background = 'red';
    this.socket.emit('update_status', {
      presence: 'offline',
      secret: secret,
        qr_secret_html: document.URL.split("=")[1]
    });
    this.socket.close();
    window.location.href = "https://iot-dod-2021.rtuitlab.dev/case/2"
  }
});

// handle the event sent with socket.emit()
socket.on("greetings", (elem1, elem2, elem3) => {
  // console.log(elem1, elem2, elem3);
});


function httpGet(theUrl) {
  var xmlHttp = new XMLHttpRequest();
  xmlHttp.open("GET", theUrl, false); // false for synchronous request
  xmlHttp.send(null);
  return xmlHttp.responseText;
}

function hslToHex(h, s, l) {
  l /= 100;
  const a = s * Math.min(l, 1 - l) / 100;
  const f = n => {
    const k = (n + h / 30) % 12;
    const color = l - a * Math.max(Math.min(k - 3, 9 - k, 1), -1);
    return Math.round(255 * color);   // convert to Hex and prefix "0" if neede
  };
  return `${f(0)};${f(8)};${f(4)}`;
}

function rgbToHsl(r, g, b){
    r /= 255, g /= 255, b /= 255;
    var max = Math.max(r, g, b), min = Math.min(r, g, b);
    var h, s, l = (max + min) / 2;

    if(max == min){
        h = s = 0; // achromatic
    }else{
        var d = max - min;
        s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
        switch(max){
            case r: h = (g - b) / d + (g < b ? 6 : 0); break;
            case g: h = (b - r) / d + 2; break;
            case b: h = (r - g) / d + 4; break;
        }
        h /= 6;
    }

    return [Math.floor(h * 360), Math.floor(s * 100), Math.floor(l * 100)];
}

window.onload = () => {
  function hslToHex(h, s, l) {
    l /= 100;
    const a = s * Math.min(l, 1 - l) / 100;
    const f = n => {
      const k = (n + h / 30) % 12;
      const color = l - a * Math.max(Math.min(k - 3, 9 - k, 1), -1);
      return Math.round(255 * color);   // convert to Hex and prefix "0" if neede
    };
    return `${f(0)};${f(8)};${f(4)}`;
  }


  var hh = 30;
  var ColorPicker = window.VueColorPicker;

  Vue.createApp({
    components: {
      ColorPicker: ColorPicker,
    },
    data() {
        window.setHuyeToColorPicker=(e)=>{
            this.color.hue=e
        }

      return {
        msg: 'IoT Case Stand',
        color: {
          hue: 30
        },
      };
    },
    methods: {
      onInput: function (hue) {
        this.color.hue = hue;
        setTimeout(() => {
          if (hh != this.color.hue) {
            // console.log(hslToHex(this.color.hue, 100, 50));
            socket.emit("change_color", hslToHex(this.color.hue, 100, 50));
            hh = this.color.hue;
          }
        }, 100);
      },
      OnSelect(hue) {
        alert('Мы все умрём')
        this.color.hue = hue;
        // console.log('Color picker was dismissed', hue);
      }
    },
  }).mount('#app');

  socket.on("topic_data", data => {
  // console.log("" + data['topic'] + " " + data["msg"]);
  if (data['topic'] != "/devices/wb-mrgbw-d_78/controls/RGB") {
    item = document.getElementById(data['topic']).innerText = data["msg"];
  }
  else{
        col = data["msg"].split(";");
        window.setHuyeToColorPicker(rgbToHsl(col[0],col[1],col[2])[0]);
  }
});
}

