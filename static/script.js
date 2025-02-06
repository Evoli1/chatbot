document.addEventListener('DOMContentLoaded', () => {
    const chatContainer = document.getElementById('chat-container');
    const chatBox = document.getElementById('chat-box');
    const userInput = document.getElementById('user-input');
    const sendButton = document.querySelector('.send-button');
    const chatButtons = document.querySelectorAll('.chat-button');
    const buttonOptions = document.getElementById('button-options');

    let userChoice = ""; // Tracks the user's initial action (e.g., literatur-suchen)

    // Open the chatbot window when clicking the logo
    document.getElementById('chatbot-logo').addEventListener('click', () => {
        chatContainer.classList.remove('hidden');
        sendHelloMessage();
    });

    // Close the chatbot window 
    document.getElementById('close-button').addEventListener('click', () => {
        chatBox.innerHTML = ''; // Clear all chat history
        chatContainer.classList.add('hidden');
    });

    // Send the initial welcome message
    function sendHelloMessage() {
        addLibbyMessage("Hallo! Ich bin Libby – dein Bibliotheksassistent. Wie kann ich dir heute helfen?");
        setTimeout(() => {
            buttonOptions.classList.remove('hidden'); // Reveal buttons
            chatButtons.forEach((button, index) => {
                button.style.animationDelay = `${index * 0.3}s`; // Stagger animation delays
                button.classList.remove('hidden'); // Ensure the buttons become visible
            });
        }, 1000); // Delay to ensure message is fully shown first
    }

    // Map button action to user-readable text
    function getUserChoice(action) {
        switch (action) {
            case "literatur-suchen":
                return "Literatur suchen";
            case "information-request":
                return "Information zur Bibliothek";
            case "literatur-vorschlagen":
                return "Literatur vorschlagen";
            default:
                return action;
        }
    }

    // Add a new message to the chat as Libby
    function addLibbyMessage(message) {
        const messageElement = document.createElement('div');
        messageElement.classList.add('chat-message', 'libby-message');
        messageElement.textContent = message;
        styleMessage(messageElement, false); // Style for Libby
        chatBox.appendChild(messageElement);
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    // Add a new message to the chat as the user
    function addUserMessage(message) {
        const messageElement = document.createElement('div');
        messageElement.classList.add('chat-message', 'user-message');
        messageElement.textContent = message;
        styleMessage(messageElement, true); // Style for user
        chatBox.appendChild(messageElement);
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    function styleMessage(element, isUser) {
        element.style.maxWidth = '80%';
        element.style.padding = '10px';
        element.style.fontSize = '16px';
        element.style.marginBottom = '10px';
        element.style.transition = 'opacity 500ms ease-in-out';
        element.style.opacity = '0';
        if (isUser) {
            element.style.backgroundColor = '#D9F0FF';
            element.style.color = '#333';
            element.style.alignSelf = 'flex-end';
        } else {
            element.style.backgroundColor = '#fff';
            element.style.color = '#333';
            element.style.marginLeft = '10px';
        }
        setTimeout(() => {
            element.style.opacity = '1';
        }, 300);
    }

    // Handle button clicks
    chatButtons.forEach(button => {
        button.addEventListener('click', () => {
            const action = button.dataset.action;
            userChoice = action; // Store the user's choice
            const userChoiceText = getUserChoice(action);

            // Display the user's input and hide the buttons
            addUserMessage(userChoiceText);
            buttonOptions.classList.add('hidden');

            // Send the action to the backend
            sendChatRequest(action);
        });
    });

    // Handle user messages sent from the input box
    userInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            sendUserInput();
        }
    });

    sendButton.addEventListener('click', sendUserInput);

    function sendUserInput() {
        const userMessage = userInput.value.trim();
        if (userMessage) {
            addUserMessage(userMessage);
            userInput.value = '';
            sendChatRequest(userMessage);
        }
    }

    function sendChatRequest(message) {
        fetch('/chat', {
            method: 'POST',
            body: new URLSearchParams({ 'user_input': message }),
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
        })
            .then(response => response.json())
            .then(data => handleChatResponse(data))
            .catch(error => {
                addLibbyMessage("Entschuldigung, es gab einen Fehler bei der Verarbeitung deiner Anfrage.");
                console.error('Error:', error);
            });
    }

    function handleChatResponse(data) {
        addLibbyMessage(data.response);
    
        if (data.books && data.books.length > 0) {
            if (userChoice === "literatur-vorschlagen" && data.descriptions) {
                displayDescriptionsAndBooks(data.descriptions, data.books).then(() => {
                    if (data.response_after_books) {
                        setTimeout(() => {
                            addLibbyMessage(data.response_after_books);
                        }, 3000);
                    }
                });
            } else if (userChoice === "literatur-suchen") {
                setTimeout(() => {
                    displayBooks(data.books);
    
                    if (data.response_after_books) {
                        setTimeout(() => {
                            addLibbyMessage(data.response_after_books);
                        }, 3000);
                    }
                }, 1300);
            }
        }
    
        if (data.follow_up && !data.books) {
            setTimeout(fetchFollowUp, 500);
        }
    }
    
    async function displayDescriptionsAndBooks(descriptions, books) {
        for (let i = 0; i < books.length; i++) {
            const description = descriptions[i];
            const book = books[i];
            addLibbyMessage(description);
            await new Promise(resolve => setTimeout(() => resolve(), 1000));
            displayBook(book);
        }
    }
    
    function displayBooks(books) {
        return new Promise((resolve) => {
            books.forEach((book, index) => {
                setTimeout(() => {
                    displayBook(book);
                    if (index === books.length - 1) {
                        resolve();
                    }
                }, index * 1000);
            });
        });
    }
    
    function displayBook(book) {
        const bookElement = document.createElement('div');
        bookElement.className = 'book-result';
        bookElement.innerHTML = `
            <img class="book-thumbnail" src="${book.image_link}" alt="Book thumbnail">
            <div class="book-details">
                <p class="book-title">${book.title}</p>
                <p class="book-authors">Autoren: ${book.authors.join(', ')}</p>
                <p class="book-type">Typ: ${book.type}</p>
                <p class="book-publisher">Verlag: ${book.publisher}</p>
                <p class="book-isbn">ISBN: ${book.isbn || 'Nicht verfügbar'}</p>
                <a class="book-link" href="https://www.google.com/search?q=isbn+${book.isbn}" target="_blank">Auf Google suchen</a>
            </div>
        `;
        chatBox.appendChild(bookElement);
        chatBox.scrollTop = chatBox.scrollHeight;
    }
    


    function fetchFollowUp() {
        fetch('/follow_up', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
        })
            .then(response => response.json())
            .then(followUpData => addLibbyMessage(followUpData.response))
            .catch(error => {
                addLibbyMessage("Entschuldigung, ich konnte die Folgefrage nicht abrufen.");
                console.error('Follow-up Error:', error);
            });
    }


    // Send the request to get more results when the user clicks "yes"
    function sendChatRequest(message) {
        fetch('/chat', {
            method: 'POST',
            body: new URLSearchParams({ 'user_input': message }),
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
        })
            .then(response => response.json())
            .then(data => handleChatResponse(data))
            .catch(error => {
                addLibbyMessage("Entschuldigung, es gab einen Fehler bei der Verarbeitung deiner Anfrage.");
                console.error('Error:', error);
            });
    }

});
