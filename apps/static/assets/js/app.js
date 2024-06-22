class Chatbox {
  constructor() {
    this.args = {
      chatBox: document.querySelector(".chatbox__support"),
      sendButton: document.querySelector(".send__button"),
      textInput: document.querySelector(".chatbox__input"),
    };

    this.state = false;
    this.messages = [];
    this.init();
  }

  init() {
    this.display();
    this.args.sendButton.addEventListener("click", () => this.onSendButton());
    this.args.textInput.addEventListener("keyup", (event) => this.onEnterPress(event));
  }

  display() {
    const { chatBox, sendButton, textInput } = this.args;

    // Remove any existing event listeners
    sendButton.removeEventListener("click", () => this.onSendButton());
    textInput.removeEventListener("keyup", (event) => this.onEnterPress(event));

    // Add new event listeners
    sendButton.addEventListener("click", () => this.onSendButton());
    textInput.addEventListener("keyup", (event) => this.onEnterPress(event));
  }

  onEnterPress(event) {
    if (event.keyCode === 13) {
      this.onSendButton();
    }
  }

  onSendButton() {
    const textInput = this.args.textInput;
    const userMessage = textInput.value.trim();
    if (userMessage === "") {
      return;
    }

    this.addMessage('User', userMessage);
    this.sendMessageToServer(userMessage);
    textInput.value = '';
  }

  sendMessageToServer(userMessage) {
    fetch($SCRIPT_ROOT + '/predict', {
      method: 'POST',
      body: JSON.stringify({ message: userMessage }),
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
      .then(data => {
        if (data.error) {
          console.error('Error:', data.error);
        } else {
          this.addMessage('Bot', data.answer);
        }
      })
      .catch((error) => {
        console.error('Error:', error);
      });
  }

  addMessage(sender, message) {
    this.messages.push({ sender, message });

    const chatmessages = this.args.chatBox.querySelector(".chatbox__messages");
    const messageElement = document.createElement('div');
    messageElement.classList.add('messages__item');
    messageElement.classList.add(sender === 'User' ? 'messages__item--operator' : 'messages__item--visitor');
    messageElement.textContent = message;

    // Insert the new message at the beginning of the chat container
    chatmessages.insertBefore(messageElement, chatmessages.firstChild);

    // Scroll to the top of the chat container
    chatmessages.scrollTop = 0;
  }

  updateChatText(userMessage, botResponse) {
    this.addMessage('User', userMessage);
    this.addMessage('Bot', botResponse);
  }

  clearChatHistory() {
    this.messages = [];
    const chatContainer = this.args.chatBox.querySelector(".chatbox__messages");
    chatContainer.innerHTML = '';
    chatContainer.scrollTop = 0;
  }

  loadChatHistory(messages) {
    this.clearChatHistory();
    messages.forEach(({ sender, message }) => {
      this.addMessage(sender === 'user' ? 'User' : 'Bot', message);
    });
  }
  
}

let chatbox;

$(document).ready(function () {
  const chatbox = new Chatbox();

  // Handle "New Chat" click
  $('#newChatButton').click(function (e) {
    e.preventDefault();
    const initialMessage = $('.chatbox__input').val();

    // Clear the chat history in the UI
    chatbox.clearChatHistory();

    // Send request to create a new chat session
    $.ajax({
      type: 'POST',
      url: '/new_chat',
      data: JSON.stringify({ initial_message: initialMessage }),
      contentType: 'application/json',
      success: function (data) {
        // Clear the input field
        $('.chatbox__input').val('');

        // If there's an initial message, send it to the new chat
        if (initialMessage.trim() !== '') {
          chatbox.sendMessageToServer(initialMessage);
        }
      },
      error: function (xhr, status, error) {
        console.error('Error creating new chat:', error);
      }
    });
  });

  // Handle loading chat history
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
          chatbox.loadChatHistory(data.messages);
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
  if (!chatbox) {
    console.error('Chatbox instance not initialized');
    return;
  }

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
        chatbox.addMessage('User', userMessage);
        chatbox.addMessage('Bot', data.answer);
      }
    })
    .catch(error => {
      console.error('Error:', error);
    });
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
  if (!chatbox) {
    console.error('Chatbox instance not initialized');
    return;
  }

  const chatContainer = document.querySelector('.chatbox__messages');
  chatContainer.innerHTML = ''; // Clear existing messages

  messages.forEach(({ sender, message }) => {
    chatbox.addMessage(sender === 'user' ? 'User' : 'Bot', message);
  });

  // Set up event listener for new user input
  const textInput = document.querySelector('.chatbox__input');
  textInput.addEventListener('keyup', handleUserInput);
}