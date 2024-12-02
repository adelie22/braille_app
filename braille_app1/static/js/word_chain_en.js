document.addEventListener('DOMContentLoaded', function () {
    let navigableItems;
    let currentIndex = 0;

    // Game state variables
    let incorrectAttempts = 0;
    let totalExchanges = 0;
    let lastExchange = { user: '', computer: '' };
    let hasSpokenNoWordMessage = false;
    // Removed gameOver flag

    // Initialize menu and navigable items
    function initializeMenu() {
        navigableItems = [
            document.getElementById('translated-word-en'),
            document.getElementById('back-to-menu-en'),
        ];

        currentIndex = 0;
        navigableItems[currentIndex].classList.add('selected');
        navigableItems[currentIndex].focus();
        speakMessage(getItemLabel(navigableItems[currentIndex]));
        updateAttemptsDisplay();
        updateExchangeDisplay();
    }

    // Speech synthesis function for auditory feedback
    function speakMessage(message) {
        console.log('Speaking message:', message); // Debugging log
        window.speechSynthesis.cancel(); // Cancel any ongoing speech
        setTimeout(() => {
            const utterance = new SpeechSynthesisUtterance(message);
            utterance.lang = 'en-US';
            window.speechSynthesis.speak(utterance);
        }, 100); // Add slight delay
    }

    // Get label for navigable items for speech feedback
    function getItemLabel(item) {
        if (item.tagName === 'INPUT' || item.tagName === 'DIV') {
            return 'Game start';
        } 
        return '';
    }

    // Update display for incorrect attempts and total exchanges
    function updateAttemptsDisplay() {
        const attemptsDisplay = document.getElementById('attempts-en');
        attemptsDisplay.innerText = `Incorrect Attempts: ${incorrectAttempts} | Total Exchanges: ${totalExchanges}`;
    }

    // Update display for the last exchange between user and computer
    function updateExchangeDisplay() {
        const exchangeElement = document.getElementById('exchange-en');
        exchangeElement.style.opacity = 0; // Hide existing word

        setTimeout(() => {
            if (lastExchange.user && lastExchange.computer) {
                exchangeElement.innerHTML = `${lastExchange.user} → ${lastExchange.computer}`;
            } else if (lastExchange.user) {
                exchangeElement.innerHTML = `${lastExchange.user} → `;
            } else if (lastExchange.computer) {
                exchangeElement.innerHTML = `→ ${lastExchange.computer}`;
            } else {
                exchangeElement.innerHTML = '';
            }

            // Add animation
            exchangeElement.style.transform = 'scale(1.2)';
            exchangeElement.style.opacity = 1; // Show new word
            setTimeout(() => {
                exchangeElement.style.transform = 'scale(1)'; // Reset scale
            }, 300);
        }, 300);
    }

    function displayTranslatedInput(translatedText, cursorPosition) {
        const translatedWordDiv = document.getElementById('translated-word-en');
    
        // Clear previous content
        translatedWordDiv.innerHTML = '';
    
        // Clean the translated text:
        // Replace non-breaking spaces with regular spaces, remove newline characters, trim, and collapse multiple spaces
        const cleanedText = translatedText.replace(/\u00A0/g, ' ').replace(/[\r\n]+/g, ' ').replace(/\s+/g, ' ').trim();
    
        // Ensure the cursor position is within bounds
        cursorPosition = Math.max(0, Math.min(cursorPosition, cleanedText.length));
    
        // Split the text around the cursor
        const beforeText = cleanedText.slice(0, cursorPosition);
        const afterText = cleanedText.slice(cursorPosition);
    
        console.log('cleanedText:', cleanedText);
        console.log('beforeText:', beforeText);
        console.log('afterText:', afterText);
        console.log('cursorPosition:', cursorPosition);
    
        // Remove extra character after cursor only if not at the end
        const afterTextContent = cursorPosition < cleanedText.length ? afterText.slice(1) : '';
    
        console.log('afterTextContent:', afterTextContent);
    
        // Create text nodes
        const beforeTextNode = document.createTextNode(beforeText);
        const cursorHighlight = document.createElement('span');
        cursorHighlight.classList.add('cursor-highlight');
        cursorHighlight.textContent = cleanedText[cursorPosition] || '';  // Highlight character at cursor
    
        const afterTextNode = document.createTextNode(afterTextContent);
    
        // Append nodes without introducing spaces
        translatedWordDiv.appendChild(beforeTextNode);
        translatedWordDiv.appendChild(cursorHighlight);
        translatedWordDiv.appendChild(afterTextNode);
    }

    // Function to display and speak status messages
    function showStatusMessage(message) {
        const statusMessageDiv = document.getElementById('status-message-en');
        if (statusMessageDiv) {
            statusMessageDiv.innerText = message;
            speakMessage(message);
        }
    }

    // Polling function to fetch Braille inputs and control signals
    function fetchBrailleInput() {
        // Removed gameOver check

        fetch('/word_chain_en/get_current_input_buffer')
            .then(response => response.json())
            .then(data => {
                const inputBuffer = data.input_buffer;
                const controlSignal = data.control_signal;
                const quitGameFlag = data.quit_game;
                const restartGameFlag = data.restart_game; // If applicable
                const cursorPosition = data.cursor_position;

                console.log('Received Braille input buffer:', inputBuffer);
                console.log('Received control signal:', controlSignal);

                // Fetch translated text if there's any input
                if (inputBuffer && inputBuffer.length > 0) {
                    fetchTranslatedText(inputBuffer, cursorPosition);
                } else {
                    displayTranslatedInput('', cursorPosition); // Clear display if no input
                }

                // Handle control signals
                if (controlSignal) {
                    handleControlSignal(controlSignal, quitGameFlag);
                }

                // If quit_game flag is true, redirect to menu
                if (quitGameFlag) {
                    quitGame();
                }

                // If restartGameFlag is true, restart the game
                if (restartGameFlag) {
                    restartGame();
                }
            })
            .catch(error => console.error('Error fetching Braille input:', error));
    }

    /**
     * Handles various control signals received from the Braille keyboard.
     * @param {string} signal - The control signal to handle.
     * @param {boolean} quit_game - Flag indicating whether to quit the game.
     **/
    function handleControlSignal(signal, quit_game) {
        console.log(`Handling control signal: ${signal}`);
        
        switch (signal) {
            case 'Enter':
                console.log("Detected 'Enter' signal. Submitting Braille word.");
                submitBrailleWord();
                break;
            case 'Left':
                // Cursor movement is handled by the backend. Optionally, provide feedback.
                speakMessage('Cursor moved left.');
                break;
            case 'Right':
                // Cursor movement is handled by the backend. Optionally, provide feedback.
                speakMessage('Cursor moved right.');
                break;
            case 'Back':
                // Deletion is handled by the backend. Optionally, provide feedback.
                speakMessage('Character deleted.');
                break;
            case 'Ctrl+Backspace':
                // Redirect to the menu
                quitGame();
                break;
            case 'Ctrl+Enter':
                console.log("Detected 'Ctrl + Enter' signal. Restarting the game.");
                restartGame();
                break;
            default:
                console.warn(`Unhandled control signal: ${signal}`);
        }
    }

    // Fetch translated text from backend
    function fetchTranslatedText(inputBuffer, cursorPosition) {
        fetch('/word_chain_en/translate_braille', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({}), // No need to send body as backend uses g.keyboard
        })
            .then(response => response.json())
            .then(data => {
                if (data.translated_text !== undefined && data.cursor_position !== undefined) {
                    displayTranslatedInput(data.translated_text, data.cursor_position);
                }
            })
            .catch(error => console.error('Error translating Braille input:', error));
    }

    // Poll every 500 milliseconds for new Braille inputs
    setInterval(fetchBrailleInput, 500);

    // Submit the translated word when 'Enter' is detected
    function submitBrailleWord() {
        const translatedWordDiv = document.getElementById('translated-word-en');
        let translatedWord = translatedWordDiv.textContent || translatedWordDiv.innerText || '';
    
        // Remove all non-breaking spaces and newline characters
        translatedWord = translatedWord.replace(/\u00A0/g, '').replace(/[\r\n]+/g, '').trim();
    
        console.log(`Translated Word before submission: "${translatedWord}"`); // Debugging line
        if (translatedWord) {
            fetch('/word_chain_en/submit_braille_word', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({}), // No need to send body as backend fetches from g.keyboard
            })
                .then(response => response.json())
                .then(data => {
                    // Clear the translated word input field after submission
                    const translatedWordDiv = document.getElementById('translated-word-en');
                    translatedWordDiv.innerHTML = '';

                    if (data.error) {
                        document.getElementById('result-en').innerText = data.error;
                        speakMessage(data.error);

                        // Increment incorrect attempts only if the word length is sufficient
                        if (translatedWord.length >= 3) {
                            incorrectAttempts += 1;
                            updateAttemptsDisplay();

                            if (incorrectAttempts >= 3) {
                                // Show status message instead of stopping the game
                                showStatusMessage('Game over. Press Ctrl + Enter to restart or Ctrl + Backspace to quit.');
                            }
                        }
                    } else {
                        document.getElementById('result-en').innerText = data.message;
                        speakMessage(`You entered: ${translatedWord}`);
                        lastExchange.user = translatedWord;
                        updateExchangeDisplay();
                        totalExchanges += 1;
                        updateAttemptsDisplay();

                        if (data.computer_word) {
                            const computerWord = data.computer_word;
                            lastExchange.computer = computerWord;
                            updateExchangeDisplay();
                            speakMessage(`Next word: ${computerWord}`);
                            totalExchanges += 1;
                            updateAttemptsDisplay();
                        }

                        if (data.game_over) {
                            showStatusMessage('Computer cannot generate a word. Press Ctrl + Enter to restart or Ctrl + Backspace to quit.');
                        }
                    }
                })
                .catch(error => {
                    console.error('Error submitting Braille word:', error);
                    speakMessage('An error occurred.');
                });
        } else {
            if (!hasSpokenNoWordMessage) {
                speakMessage('No word to submit.');
                hasSpokenNoWordMessage = true;  // Set the flag to true
        }
    }
}

    // Function to display and speak status messages
    function showStatusMessage(message) {
        const statusMessageDiv = document.getElementById('status-message-en');
        if (statusMessageDiv) {
            statusMessageDiv.innerText = message;
            speakMessage(message);
        }
    }

    // Restart the game
    function restartGame() {
        fetch('/word_chain_en/reset', {
            method: 'POST',
        })
            .then((response) => response.json())
            .then((data) => {
                console.log(data.message);
                speakMessage('Game has been restarted.');
                // Reset flag on restart
                hasSpokenNoWordMessage = false;
                incorrectAttempts = 0; // Reset incorrect attempts
                totalExchanges = 0; // Reset total exchanges
                lastExchange = { user: '', computer: '' }; // Reset last exchanges
                updateAttemptsDisplay();
                updateExchangeDisplay();
                showStatusMessage('Game has been restarted.');
                // Optionally, reload the page to reset the game state
                window.location.reload();
            })
            .catch((error) => {
                console.error('Error resetting game:', error);
                speakMessage('An error occurred while restarting the game.');
            });
    }

    // Quit the game and return to menu
    function quitGame() {
        speakMessage('Exiting the game. Returning to the menu.');
        window.location.href = "/word_chain_menu"; // Update with actual menu URL
    }

    // Initialize the game on page load
    function initializeGame() {
        // Optionally, reset the game state on initialization
        fetch('/word_chain_en/reset', {
            method: 'POST',
        })
            .then((response) => response.json())
            .then((data) => {
                console.log(data.message);
                initializeMenu();
            })
            .catch((error) => {
                console.error('Error resetting game:', error);
                speakMessage('An error occurred while initializing the game.');
                initializeMenu(); // Attempt to initialize even if reset fails
            });
    }

    // Start the game
    initializeGame();
});