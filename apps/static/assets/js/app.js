const services = {
  english: [
    "Barangay Clearance",
    "Barangay Indigency Certificate",
    "Solo Parents Certificate",
    "No Fix Income Certificate",
    "Unable to Vote Certificate",
    "Business Permit",
    "Health Certificate",
    "First-Time Job Seeker Certificate",
    "Late Registration Certificate"
  ],
  tagalog: [
    "Barangay Clearance",
    "Barangay Indigency Certificate",
    "Certificate of Residency",
    "Solo Parents Certificate",
    "No Fix Income Certificate",
    "Business Closure Certification",
    "Unable to Vote Certificate",
    "Business Permit",
    "Health Certificate",
    "First-Time Job Seeker Certificate",
    "Late Registration Certificate"
  ]
};

class AnnouncementManager {
  constructor() {
    this.currentAnnouncements = new Set();
  }

  setAnnouncement(message) {
    this.currentAnnouncements.add(message);
  }

  getAnnouncements() {
    return Array.from(this.currentAnnouncements);
  }

  clearAnnouncements() {
    this.currentAnnouncements.clear();
  }

  hasAnnouncement(message) {
    return this.currentAnnouncements.has(message);
  }
}

class Chatbox {
  constructor() {
    this.args = {
      chatBox: document.querySelector(".chatbox__support"),
      sendButton: document.querySelector(".send__button"),
      textInput: document.querySelector(".chatbox__input"),
    };

    this.announcementManager = new AnnouncementManager();
    this.checkForAnnouncement();
    this.typingLoader = null;
    this.handleResize = this.handleResize.bind(this);
    window.addEventListener('resize', this.handleResize);
    this.choicesContainer = this.args.chatBox.querySelector(".chatbox__choices");
    this.setupChoices();
    this.userLanguagePreference = this.args.chatBox.dataset.languagePreference;
    this.state = false;
    this.messages = [];
    this.init();
  }

  handleResize() {
    this.setupChoices();
  }

  checkForAnnouncement() {
    fetch($SCRIPT_ROOT + '/api/current_announcement')
      .then(response => response.json())
      .then(data => {
        if (data.announcements && data.announcements.length > 0) {
          data.announcements.forEach(announcement => {
            if (!this.announcementManager.hasAnnouncement(announcement)) {
              this.announcementManager.setAnnouncement(announcement);
              this.displayAnnouncement(announcement);
            }
          });
        }
      })
      .catch(error => console.error('Error fetching announcement:', error));
  }

  displayAnnouncement(announcement) {
    if (announcement) {
      this.addMessage('Bot', `ANNOUNCEMENT: ${announcement}`);
    }
  }

  destroy() {
    // ... other cleanup code ...
    window.removeEventListener('resize', this.handleResize);
  }

  init() {
    this.display();
    this.setupChoices();
    this.checkForAnnouncement(); // Call this only once
    this.args.sendButton.addEventListener("click", () => this.onSendButton());
    this.args.textInput.addEventListener("keyup", (event) => this.onEnterPress(event));
  }

  setupChoices() {
    const languageServices = this.userLanguagePreference === 'tagalog' ? services.tagalog : services.english;
    const screenWidth = window.innerWidth;
    let choiceCount;

    if (screenWidth > 768) {
      choiceCount = 5;
    } else if (screenWidth > 480) {
      choiceCount = 3;
    } else {
      choiceCount = 2;
    }

    const randomChoices = this.getRandomChoices(languageServices, choiceCount);

    this.choicesContainer.innerHTML = '';
    randomChoices.forEach(choice => {
      const button = document.createElement('button');
      button.textContent = choice;
      button.addEventListener('click', () => this.onChoiceClick(choice));
      this.choicesContainer.appendChild(button);
    });
  }

  getRandomChoices(array, count) {
    const shuffled = array.sort(() => 0.5 - Math.random());
    return shuffled.slice(0, count);
  }

  onChoiceClick(choice) {
    this.args.textInput.value = `How can I get a ${choice}?`;
    if (this.userLanguagePreference === 'tagalog') {
      this.args.textInput.value = `Paano ako makakakuha ng ${choice}?`;
    }
    this.onSendButton();
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
    // Show typing indicator
    this.addMessage('Bot', 'typing');
    const startTime = Date.now();

    fetch($SCRIPT_ROOT + '/predict', {
      method: 'POST',
      body: JSON.stringify({
        message: userMessage
      }),
      mode: 'cors',
      headers: {
        'Content-Type': 'application/json'
      },
      credentials: 'include'
    })
      .then(response => response.json())
      .then(data => {
        const endTime = Date.now();
        const elapsedTime = endTime - startTime;
        const minimumLoaderTime = 1000; // 1 second in milliseconds

        const hideLoader = () => {
          // Remove typing indicator
          if (this.typingLoader && this.typingLoader.parentNode) {
            this.typingLoader.parentNode.removeChild(this.typingLoader);
            this.typingLoader = null;
          }

          if (data.error) {
            console.error('Error:', data.error);
          } else {
            if (data.ticket_image) {
              this.addMessage('Bot', {
                message: data.message || 'Here is your appointment ticket:',
                ticket_image: data.ticket_image
              });
            } else {
              this.addMessage('Bot', data.message || data.answer);
            }
          }
        };

        if (elapsedTime < minimumLoaderTime) {
          setTimeout(hideLoader, minimumLoaderTime - elapsedTime);
        } else {
          hideLoader();
        }
      })
      .catch((error) => {
        // Remove typing indicator
        if (this.typingLoader && this.typingLoader.parentNode) {
          this.typingLoader.parentNode.removeChild(this.typingLoader);
          this.typingLoader = null;
        }
        console.error('Error:', error);
      });
  }

  confirmAppointment(appointmentData) {
    const confirmMessage = `Please confirm your appointment details:`;
    this.addMessage('Bot', confirmMessage);

    const ticket = generate_appointment_ticket(appointmentData);
    this.addStyledMessage('Bot', ticket);

    this.addMessage('Bot', "Type 'confirm' to schedule this appointment or 'cancel' to start over.");
  }

  addStyledMessage(sender, message) {
    const chatmessages = this.args.chatBox.querySelector(".chatbox__messages");
    const messageElement = document.createElement('div');
    messageElement.classList.add('messages__item');
    messageElement.classList.add(sender === 'User' ? 'messages__item--operator' : 'messages__item--visitor');

    // Check if the message contains HTML (like an image tag)
    if (message.startsWith('<') && message.endsWith('>')) {
      messageElement.innerHTML = message;
    } else {
      messageElement.textContent = message;
    }

    chatmessages.insertBefore(messageElement, chatmessages.firstChild);
    chatmessages.scrollTop = 0;
  }

  updateCalendar() {
    fetch($SCRIPT_ROOT + '/get_appointments')
      .then(response => response.json())
      .then(appointments => {
        if (window.calendar) {
          window.calendar.removeAllEvents();
          window.calendar.addEventSource(appointments);
        }
      })
      .catch((error) => {
        console.error('Error updating calendar:', error);
      });
  }

  addMessage(sender, message) {
    const chatmessages = this.args.chatBox.querySelector(".chatbox__messages");
    const messageElement = document.createElement('div');
    messageElement.classList.add('messages__item');

    if (sender === 'Bot' && message === 'typing') {
      messageElement.classList.add('messages__item--visitor', 'typing-loader');
      messageElement.innerHTML = '<span></span><span></span><span></span>';
      this.typingLoader = messageElement;
    } else {
      messageElement.classList.add(sender === 'User' ? 'messages__item--operator' : 'messages__item--visitor');

      if (typeof message === 'object' && message.ticket_image) {
        const ticketImage = document.createElement('img');
        ticketImage.src = `data:image/png;base64,${message.ticket_image}`;
        ticketImage.alt = 'Appointment Ticket';
        ticketImage.classList.add('ticket-image');

        const downloadButton = document.createElement('a');
        downloadButton.href = ticketImage.src;
        downloadButton.download = 'appointment_ticket.png';
        downloadButton.textContent = 'Download Ticket';
        downloadButton.classList.add('btn', 'btn-primary', 'mt-2');

        messageElement.appendChild(document.createTextNode(message.message));
        messageElement.appendChild(document.createElement('br'));
        messageElement.appendChild(ticketImage);
        messageElement.appendChild(document.createElement('br'));
        messageElement.appendChild(downloadButton);
      } else {
        messageElement.textContent = message;
      }
    }

    chatmessages.insertBefore(messageElement, chatmessages.firstChild);
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
    this.setupChoices();
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

        window.location.reload();
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
    body: JSON.stringify({
      message: userMessage,
      language: chatbox.userLanguagePreference
    })
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


function generate_appointment_ticket(appointment_data) {
  return null; // We're now using an image for the ticket
}