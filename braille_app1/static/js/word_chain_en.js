// static/js/word_chain_en.js

document.addEventListener('DOMContentLoaded', function () {
    let navigableItems;
    let currentIndex = 0;

    // Game state variables
    let incorrectAttempts = 0;
    let totalExchanges = 0;
    let lastExchange = { user: '', computer: '' };
    let gameOver = false;

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
        if (item.tagName === 'INPUT') {
            return 'Translated Word Input Field';
        } else if (item.id === 'back-to-menu-en') {
            return 'Back to Menu Button';
        } else if (item.id === 'retry-button-en') {
            return 'Retry Button';
        } else if (item.id === 'cancel-button-en') {
            return 'Cancel Button';
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

    // Display translated word from Braille inputs
    function displayTranslatedInput(translatedText) {
        const translatedWordInput = document.getElementById('translated-word-en');
        translatedWordInput.value = translatedText;
    }

    // Polling function to fetch Braille inputs and control signals
    function fetchBrailleInput() {
        if (gameOver) return; // Do not poll if game is over

        fetch('/word_chain_en/get_current_input_buffer')
            .then(response => response.json())
            .then(data => {
                const inputBuffer = data.input_buffer;
                const controlSignal = data.control_signal;

                console.log('Received Braille input buffer:', inputBuffer);
                console.log('Received control signal:', controlSignal);

                // Fetch translated text if there's any input
                if (inputBuffer && inputBuffer.length > 0) {
                    fetchTranslatedText(inputBuffer);
                } else {
                    displayTranslatedInput(''); // Clear display if no input
                }

                // If 'Enter' signal is detected, submit the word
                if (controlSignal) {
                    handleControlSignal(controlSignal);
                }
            })
            .catch(error => console.error('Error fetching Braille input:', error));
    }
        /**
     * Handles various control signals received from the Braille keyboard.
     *  {string} signal - The control signal to handle.
     **/
    function handleControlSignal(signal) {
        switch (signal) {
            case 'Enter':
                submitBrailleWord();
                break;
            case 'Left':
                navigateMenu('left');
                break;
            case 'Right':
                navigateMenu('right');
                break;
            case 'Ctrl+Backspace':
                quitGame();
                break;
            case 'Back':
                deleteLastCharacter();
                break;
            default:
                console.warn(`Unhandled control signal: ${signal}`);
        }
    }

    /**
     * Deletes the last character from the translated word input field.
     */
    function deleteLastCharacter() {
        const translatedWordInput = document.getElementById('translated-word-en');
        let currentValue = translatedWordInput.value;
        translatedWordInput.value = currentValue.slice(0, -1);
        speakMessage('Character deleted.');
    }

    // Fetch translated text from backend
    function fetchTranslatedText(inputBuffer) {
        fetch('/word_chain_en/translate_braille', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({}), // No need to send body as backend uses g.keyboard
        })
            .then(response => response.json())
            .then(data => {
                if (data.translated_text) {
                    displayTranslatedInput(data.translated_text);
                }
            })
            .catch(error => console.error('Error translating Braille input:', error));
    }

    // Poll every second for new Braille inputs
    setInterval(fetchBrailleInput, 1000);

    // Submit the translated word when 'Enter' is detected
    function submitBrailleWord() {
        const translatedWord = document.getElementById('translated-word-en').value.trim();
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
                    document.getElementById('translated-word-en').value = '';
                    document.getElementById('translated-word-en').focus();

                    if (data.error) {
                        document.getElementById('result-en').innerText = data.error;
                        speakMessage(data.error);

                        // Increment incorrect attempts only if the word length is sufficient
                        if (translatedWord.length >= 3) {
                            incorrectAttempts += 1;
                            updateAttemptsDisplay();

                            if (incorrectAttempts >= 3) {
                                gameOver = true;
                                speakMessage('Game over. Press Enter to continue or Escape to quit.');
                                openGameOverPopup();
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
                            gameOver = true;
                            speakMessage('Computer cannot generate a word. Press Enter to continue or Escape to quit.');
                            openGameOverPopup();
                        }
                    }
                })
                .catch(error => {
                    console.error('Error submitting Braille word:', error);
                    speakMessage('An error occurred.');
                });
        } else {
            speakMessage('No word to submit.');
        }
    }

    // Navigation between menu items
    function navigateMenu(direction) {
        navigableItems[currentIndex].classList.remove('selected');
        window.speechSynthesis.cancel(); // Cancel current speech

        // Update index based on direction
        if (direction === 'left') {
            currentIndex = (currentIndex - 1 + navigableItems.length) % navigableItems.length;
        } else if (direction === 'right') {
            currentIndex = (currentIndex + 1) % navigableItems.length;
        }

        // Highlight the new selected item
        navigableItems[currentIndex].classList.add('selected');
        navigableItems[currentIndex].focus();
        speakMessage(getItemLabel(navigableItems[currentIndex]));
    }

    // Keyboard event listener for navigation and submission
    document.addEventListener('keydown', (event) => {
        if (document.getElementById('popup-en').style.display === 'block') {
            // Ignore key events when popup is active
            return;
        }

        if (gameOver) {
            // Ignore key events when game is over
            return;
        }

        if (event.key === 'ArrowLeft') {
            event.preventDefault();
            navigateMenu('left');
        } else if (event.key === 'ArrowRight') {
            event.preventDefault();
            navigateMenu('right');
        } else if (event.key === 'Enter') {
            const activeElement = navigableItems[currentIndex];
            if (activeElement.id === 'back-to-menu-en') {
                // Back to Menu button clicked
                window.location.href = "/word_chain_menu"; // Update with actual menu URL
            }
            // No action needed for 'translated-word-en' as submission is handled via 'Enter' signal
        }
    });

    // Popup button click event listeners
    document.getElementById('retry-button-en').addEventListener('click', () => {
        restartGame();
    });

    document.getElementById('cancel-button-en').addEventListener('click', () => {
        quitGame();
    });

    // Open Game Over Popup
    function openGameOverPopup() {
        const popup = document.getElementById('popup-en');
        const message = document.getElementById('popup-message-en');

        if (incorrectAttempts >= 3) {
            message.innerText = 'Game over. Press Enter to continue or Escape to quit.';
        } else {
            message.innerText = 'Computer cannot generate a word. Press Enter to continue or Escape to quit.';
        }

        popup.style.display = 'block';
        navigableItems = [
            document.getElementById('retry-button-en'),
            document.getElementById('cancel-button-en'),
        ];
        currentIndex = 0;
        navigableItems[currentIndex].classList.add('selected');
        navigableItems[currentIndex].focus();
        speakMessage(getItemLabel(navigableItems[currentIndex]));
    }

    // Close Game Over Popup
    function closeGameOverPopup() {
        const popup = document.getElementById('popup-en');
        popup.style.display = 'none';
        navigableItems.forEach(item => item.classList.remove('selected'));
        currentIndex = 0;
        initializeMenu();
    }

    // Handle popup navigation and actions
    function handlePopupNavigationEn(e) {
        e.preventDefault();
        if (!navigableItems) return;

        if (e.key === 'ArrowLeft') {
            navigatePopupEn('left');
        } else if (e.key === 'ArrowRight') {
            navigatePopupEn('right');
        } else if (e.key === 'Enter') {
            const activeElement = navigableItems[currentIndex];
            if (activeElement.id === 'retry-button-en') {
                // Retry the game
                restartGame();
            } else if (activeElement.id === 'cancel-button-en') {
                // Quit the game
                quitGame();
            }
        } else if (e.key === 'Escape') {
            // Escape key to quit the game
            quitGame();
        }
    }

    // Navigation within the popup
    function navigatePopupEn(direction) {
        navigableItems[currentIndex].classList.remove('selected');
        window.speechSynthesis.cancel(); // Cancel current speech

        // Update index based on direction
        if (direction === 'left') {
            currentIndex = (currentIndex - 1 + navigableItems.length) % navigableItems.length;
        } else if (direction === 'right') {
            currentIndex = (currentIndex + 1) % navigableItems.length;
        }

        // Highlight the new selected popup item
        navigableItems[currentIndex].classList.add('selected');
        navigableItems[currentIndex].focus();
        speakMessage(getItemLabel(navigableItems[currentIndex]));
    }

    // Additional key event listener for popup navigation
    document.addEventListener('keydown', (event) => {
        if (document.getElementById('popup-en').style.display === 'block') {
            if (['ArrowLeft', 'ArrowRight', 'Enter', 'Escape'].includes(event.key)) {
                handlePopupNavigationEn(event);
            }
        }
    });

    // Restart the game
    function restartGame() {
        fetch('/word_chain_en/reset', {
            method: 'POST',
        })
            .then((response) => response.json())
            .then((data) => {
                console.log(data.message);
                speakMessage('Game has been restarted.');
                incorrectAttempts = 0; // Reset incorrect attempts
                totalExchanges = 0; // Reset total exchanges
                lastExchange = { user: '', computer: '' }; // Reset last exchanges
                updateAttemptsDisplay();
                updateExchangeDisplay();
                closeGameOverPopup();
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
