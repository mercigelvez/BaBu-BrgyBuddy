class Chatbox {
  constructor() {
    this.args = {
      chatBox: document.querySelector(".chatbox__support"),
      sendButton: document.querySelector(".send__button"),
      textInput: document.querySelector(".chatbox__input"),
    };

    this.state = false;
    this.messages = [];
  }

  display() {
    const { chatBox, sendButton, textInput } = this.args;

    sendButton.addEventListener("click", () => this.onSendButton());

    textInput.addEventListener("keyup", ({ key }) => {
      if (key === "Enter") {
        this.onSendButton();
      }
    });
  }

  onSendButton() {
    const textInput = this.args.textInput;
    let text1 = textInput.value;
    if (text1 === "") {
      return;
    }

    let msg1 = { name: "User", message: text1 };
    this.messages.push(msg1);

    // http://127.0.0.1:5000/predict
    fetch($SCRIPT_ROOT + '/predict', {
        method: 'POST',
        body: JSON.stringify({ message: text1 }),
        mode: 'cors',
        headers: {
            'Content-Type': 'application/json'
        },
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error ${response.status}`);
        }
        return response.json();
    })
    .then(r => {
        if (r.error) {
            console.error('Error:', r.error);
        } else {
            let msg2 = { name: "Babu", message: r.answer };
            this.messages.push(msg2);
            this.updateChatText();
            textInput.value = '';
        }
    })
    .catch((error) => {
        console.error('Error:', error);
        this.updateChatText();
        textInput.value = '';
    });
  }

  updateChatText() {
    var html = "";
    this.messages
      .slice()
      .reverse()
      .forEach(function (item) {
        if (item.name === "Babu") {
          html +=
            '<div class="messages__item messages__item--visitor">' +
            item.message +
            "</div>";
        } else {
          html +=
            '<div class="messages__item messages__item--operator">' +
            item.message +
            "</div>";
        }
      });

    const chatmessages = this.args.chatBox.querySelector(".chatbox__messages");
    chatmessages.innerHTML = html;
  }
}

document.addEventListener("DOMContentLoaded", () => {
  const chatbox = new Chatbox();
  chatbox.display();
});
