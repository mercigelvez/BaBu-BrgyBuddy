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
  
    // Send the message to the server
    fetch($SCRIPT_ROOT + '/predict', {
      method: 'POST',
      body: JSON.stringify({ message: text1, user_id: 'current_user_id' }), // Replace 'current_user_id' with actual user ID
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
          // Update the chat text with the user's message and the bot's response
          this.updateChatText(text1, r.answer);
          textInput.value = '';
        }
      })
      .catch((error) => {
        console.error('Error:', error);
        textInput.value = '';
      });
  }

  updateChatText(userMessage, botResponse) {
    this.messages.push({ name: 'User', message: userMessage });
    this.messages.push({ name: 'Bot', message: botResponse });
  
    var html = "";
    this.messages
      .slice()
      .reverse()
      .forEach(function (item) {
        if (item.name === "Bot") {
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

$(document).ready(function () {
  const chatbox = new Chatbox();
  chatbox.display();

  // Handle "New Chat" click
  $('a[href="#"]').click(function (e) {
    e.preventDefault();
    $.ajax({
      type: 'POST',
      url: '/new_chat',
      data: {
        user_id: 'current_user_id'  // Replace with the actual user ID
      },
      success: function (data) {
        // Clear the chat container
        $('.chatboxmessages').html('');
      },
      error: function (xhr, status, error) {
        console.error(error);
      }
    });
  });

  // Handle chat history title click
  $('a[href="#"]').click(function (e) {
    e.preventDefault();
    $.ajax({
      type: 'GET',
      url: '/get_chat_history',
      data: {
        user_id: 'current_user_id'  // Replace with the actual user ID
      },
      success: function (data) {
        // Render the chat history in the chat container
        var chatContainer = $('.chatboxmessages');
        chatContainer.html('');
        var messages = data.messages;
        $.each(messages, function (index, message) {
          var sender = message.sender;
          var content = message.message;
          var messageElement = $('<div>').text(sender + ': ' + content);
          chatContainer.append(messageElement);
        });
      },
      error: function (xhr, status, error) {
        console.error(error);
      }
    });
  });
});