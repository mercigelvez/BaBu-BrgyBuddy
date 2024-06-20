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

  clearChatHistory() {
    this.messages = [];
    const chatContainer = this.args.chatBox.querySelector(".chatbox__messages");
    chatContainer.innerHTML = '';
  }

  display() {
    const { chatBox, sendButton, textInput } = this.args;
  
    sendButton.addEventListener("click", () => this.onSendButton());
  
    // Set the data-event-listener attribute for the textInput
    const handleUserInputNew = handleUserInput.bind(null);
    textInput.setAttribute('data-event-listener', handleUserInputNew);
    textInput.addEventListener("keyup", handleUserInputNew);
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
    const newUserMessage = { name: 'User', message: userMessage };
    const newBotMessage = { name: 'Bot', message: botResponse };
  
    this.messages.push(newUserMessage);
    this.messages.push(newBotMessage);
  
    const chatmessages = this.args.chatBox.querySelector(".chatbox__messages");
    chatmessages.innerHTML = ''; // Clear existing messages
  
    this.messages.forEach(function (item) {
      const messageElement = document.createElement('div');
      messageElement.classList.add('messages__item');
  
      if (item.name === "Bot") {
        messageElement.classList.add('messages__item--visitor');
      } else {
        messageElement.classList.add('messages__item--operator');
      }
  
      messageElement.textContent = item.message;
      chatmessages.appendChild(messageElement);
    });
  }
}

$(document).ready(function () {
  const chatbox = new Chatbox();
  chatbox.display();

  // Handle "New Chat" click
  $('#newChatButton').click(function (e) {
    e.preventDefault();
    const initialMessage = $('.chatbox__input').val();

    chatbox.clearChatHistory();

    $.ajax({
      type: 'POST',
      url: '/new_chat',
      data: {
        initial_message: initialMessage
      },
      success: function (data) {
        // Clear the chat container
        $('.chatbox__messages').html('');
        // Clear the input field
        $('.chatbox__input').val('');
      },
      error: function (xhr, status, error) {
        console.error(error);
      }
    });
  });

  $('a[data-chat-history-id]').click(function (e) {
    e.preventDefault();
    const chatHistoryId = $(this).data('chat-history-id');

    // Make an AJAX request to retrieve chat history
    fetch(`/get_chat_history?chat_history_id=${chatHistoryId}`)
      .then(response => response.json())
      .then(data => {
        if (data.error) {
          console.error(data.error);
        } else {
          // Update the chatbox with the chat history messages
          updateChatboxWithHistory(data.messages);

          // Set up event listeners for new user input
          const textInput = document.querySelector('.chatbox__input');
          textInput.addEventListener('keyup', handleUserInput);
        }
      })
      .catch(error => console.error(error));
  });

});

function updateChatboxWithHistory(messages) {
  const chatContainer = document.querySelector('.chatbox__messages');
  chatContainer.innerHTML = ''; // Clear existing messages

  messages.forEach(({ sender, message }) => {
    const messageElement = document.createElement('div');
    messageElement.classList.add('messages__item');
    messageElement.classList.add(sender === 'user' ? 'messages__item--operator' : 'messages__item--visitor');
    messageElement.textContent = message;
    chatContainer.appendChild(messageElement);
  });

  // Remove existing event listener if present
  const textInput = document.querySelector('.chatbox__input');
  const handleUserInputExisting = textInput.getAttribute('data-event-listener');
  if (handleUserInputExisting) {
    textInput.removeEventListener('keyup', handleUserInputExisting);
  }

  // Set up event listener for new user input
  const handleUserInputNew = handleUserInput.bind(null);
  textInput.setAttribute('data-event-listener', handleUserInputNew);
  textInput.addEventListener('keyup', handleUserInputNew);
}

function handleUserInput(event) {
  if (event.key === 'Enter') {
    const textInput = event.target;
    const userMessage = textInput.value.trim();

    if (userMessage) {
      sendMessageToServer(userMessage);
      textInput.value = '';
    }
  }
}

function sendMessageToServer(userMessage) {
  fetch('/predict', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ message: userMessage })
  })
    .then(response => response.json())
    .then(data => {
      if (data.error) {
        console.error(data.error);
      } else {
        appendMessageToChatbox('user', userMessage);
        appendMessageToChatbox('bot', data.answer);
      }
    })
    .catch(error => console.error(error));
}

function appendMessageToChatbox(sender, message) {
  const chatContainer = document.querySelector('.chatbox__messages');
  const messageElement = document.createElement('div');
  messageElement.classList.add('messages__item');
  messageElement.classList.add(sender === 'user' ? 'messages__item--operator' : 'messages__item--visitor');
  messageElement.textContent = message;
  chatContainer.appendChild(messageElement);
  chatContainer.scrollTop = chatContainer.scrollHeight;
}

function updateChatboxWithHistory(messages) {
  const chatContainer = document.querySelector('.chatbox__messages');
  chatContainer.innerHTML = ''; // Clear existing messages

  messages.forEach(({ sender, message }) => {
    const messageElement = document.createElement('div');
    messageElement.classList.add('messages__item');
    messageElement.classList.add(sender === 'user' ? 'messages__item--operator' : 'messages__item--visitor');
    messageElement.textContent = message;
    chatContainer.appendChild(messageElement);
  });

  // Set up event listener for new user input
  const textInput = document.querySelector('.chatbox__input');
  textInput.addEventListener('keyup', handleUserInput);
}

