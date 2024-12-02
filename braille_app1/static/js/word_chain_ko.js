// static/js/word_chain_ko.js

document.addEventListener('DOMContentLoaded', function () {
    let navigableItems;
    let currentIndex = 0;

    // 게임 상태 변수
    let incorrectAttempts = 0;
    let totalExchanges = 0;
    let lastExchange = { user: '', computer: '' };
    let hasSpokenNoWordMessage = false;

    // // 최신 입력 버퍼 및 번역된 텍스트 저장 변수
    // let currentInputBuffer = [];
    // let translatedText = '';

    // 메뉴 및 네비게이션 항목 초기화 함수
    function initializeMenu() {
        navigableItems = [
            document.getElementById('translated-word-ko'),
            document.getElementById('back-to-menu-ko'),
        ];

        currentIndex = 0;
        navigableItems[currentIndex].classList.add('selected');
        navigableItems[currentIndex].focus();
        speakMessage(getItemLabel(navigableItems[currentIndex]));
        updateAttemptsDisplay();
        updateExchangeDisplay();
    }

    // 음성 합성 함수 (한국어)
    function speakMessage(message) {
        console.log('Speaking message:', message); // 디버깅 로그
        window.speechSynthesis.cancel(); // 이전 음성 중단
        setTimeout(() => {
            const utterance = new SpeechSynthesisUtterance(message);
            utterance.lang = 'ko-KR';
            window.speechSynthesis.speak(utterance);
        }, 100); // 지연 시간 추가
    }

    // 네비게이션 항목의 라벨 가져오기
    function getItemLabel(item) {
        if (item.tagName === 'INPUT' || item.tagName === 'DIV') {
            return '게임 시작'; // 'Game start'의 한국어
        }
        return '';
    }

    // 틀린 시도 및 총 교환 횟수 업데이트 함수
    function updateAttemptsDisplay() {
        const attemptsDisplay = document.getElementById('attempts-ko');
        attemptsDisplay.innerText = `틀린 횟수: ${incorrectAttempts} | 주고 받은 횟수: ${totalExchanges}`;
    }

    // 마지막 교환 내용 업데이트 함수
    function updateExchangeDisplay() {
        const exchangeElement = document.getElementById('exchange-ko');
        exchangeElement.style.opacity = 0; // 기존 단어 숨기기

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

            // 애니메이션 적용
            exchangeElement.style.transform = 'scale(1.2)';
            exchangeElement.style.opacity = 1; // 새로운 단어 보여주기
            setTimeout(() => {
                exchangeElement.style.transform = 'scale(1)'; // 크기 원상복구
            }, 300);
        }, 300);
    }

    // /**
    //  * 번역된 텍스트를 화면에 표시하는 함수 (수정됨)
    //  * @param {string} translatedTextFromBackend - 백엔드에서 번역된 전체 텍스트
    //  * @param {number} cursorPosition - 커서 위치
    //  */
    function displayTranslatedInput(translatedText, cursorPosition) {
        const translatedWordDiv = document.getElementById('translated-word-ko');

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


    /**
     * 점자 입력 및 컨트롤 신호 폴링 함수
     * 주기적으로 백엔드로부터 입력 버퍼와 제어 신호를 가져옴
     */
    function fetchBrailleInput() {
        fetch('/word_chain/get_current_input_buffer') // 수정된 엔드포인트
            .then(response => response.json())
            .then(data => {
                const inputBuffer = data.input_buffer;
                const controlSignal = data.control_signal;
                const quitGameFlag = data.quit_game;
                const restartGameFlag = data.restart_game; // 필요시 사용
                const cursorPosition = data.cursor_position;

                console.log('Received Braille input buffer:', inputBuffer);
                console.log('Received control signal:', controlSignal);

                // // 최신 입력 버퍼 저장
                // currentInputBuffer = inputBuffer;

                // 입력이 있는 경우 번역된 텍스트 가져오기
                if (inputBuffer && inputBuffer.length > 0) {
                    fetchTranslatedText(inputBuffer, cursorPosition);
                } else {
                    // 입력이 없으면 화면 지우기
                    displayTranslatedInput('', cursorPosition);
                }

                // 컨트롤 신호 처리
                if (controlSignal) {
                    handleControlSignal(controlSignal, quitGameFlag);
                }

                // 게임 종료 플래그 처리
                if (quitGameFlag) {
                    quitGame();
                }

                // 게임 재시작 플래그 처리 (필요 시)
                if (restartGameFlag) {
                    restartGame();
                }
            })
            .catch(error => console.error('Error fetching Braille input:', error));
    }

    /**
     * 컨트롤 신호 처리 함수
     * @param {string} signal - 처리할 신호
     * @param {boolean} quit_game - 게임 종료 플래그
     */
    function handleControlSignal(signal, quit_game) {
        console.log(`Handling control signal: ${signal}`);

        switch (signal) {
            case 'Enter':
                console.log("Detected 'Enter' signal. Submitting Braille word.");
                submitBrailleWord();
                break;
            case 'Left':
                // 커서 이동은 백엔드에서 처리. 필요 시 피드백 제공
                speakMessage('커서가 왼쪽으로 이동했습니다.');
                break;
            case 'Right':
                // 커서 이동은 백엔드에서 처리. 필요 시 피드백 제공
                speakMessage('커서가 오른쪽으로 이동했습니다.');
                break;
            case 'Back':
                // 삭제는 백엔드에서 처리. 필요 시 피드백 제공
                speakMessage('문자가 삭제되었습니다.');
                break;
            case 'Ctrl+Backspace':
                // 게임 종료 및 메뉴로 돌아가기
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

    // /**
    //  * 번역된 텍스트를 백엔드로부터 받아오는 함수 (수정됨)
    //  * @param {Array} inputBuffer - 현재 입력된 점자 비트 리스트
    //  * @param {number} cursorPosition - 현재 커서 위치
    //  */
    function fetchTranslatedText(inputBuffer, cursorPosition) {
        console.log('Fetching translated text with input_buffer:', inputBuffer);
        fetch('/word_chain/translate_braille', { // 수정된 엔드포인트
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({}), // 입력 버퍼 전송
        })
            .then(response => response.json())
            .then(data => {
                console.log('Translated text data:', data);
                if (data.translated_text !== undefined && data.cursor_position !== undefined) {
                    displayTranslatedInput(data.translated_text, data.cursor_position);
                }
            })
            .catch(error => console.error('Error translating Braille input:', error));
    }

    /**
     * 점자 단어 제출 함수 (수정됨)
     * 현재 입력 버퍼를 백엔드로 전송하여 단어를 제출
     */
    function submitBrailleWord() {
        const translatedWordDiv = document.getElementById('translated-word-ko');
        let translatedWord = translatedWordDiv.textContent || translatedWordDiv.innerText || '';

        // Remove all non-breaking spaces and newline characters
        translatedWord = translatedWord.replace(/\u00A0/g, '').replace(/[\r\n]+/g, '').trim();

        console.log(`Translated Word before submission: "${translatedWord}"`); // Debugging line
        if (translatedWord) {
            fetch('/word_chain/submit_braille_word', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({}), // No need to send body as backend fetches from g.keyboard
            })
                .then(response => response.json())
                .then(data => {
                    // Clear the translated word input field after submission
                    const translatedWordDiv = document.getElementById('translated-word-ko');
                    translatedWordDiv.innerHTML = '';

                    if (data.error) {
                        document.getElementById('result-ko').innerText = data.error;
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
                        document.getElementById('result-ko').innerText = data.message;
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
    // 상태 메시지 표시 및 음성 출력 함수
    function showStatusMessage(message) {
        const statusMessageDiv = document.getElementById('status-message-ko');
        if (statusMessageDiv) {
            statusMessageDiv.innerText = message;
            speakMessage(message);
        }
    }

    /**
     * 게임 재시작 함수
     * 백엔드의 히스토리를 초기화하고 게임 상태를 재설정
     */
    function restartGame() {
        fetch('/word_chain/reset', { // 수정된 엔드포인트
            method: 'POST',
        })
            .then((response) => response.json())
            .then((data) => {
                console.log(data.message);
                speakMessage('게임이 재시작되었습니다.');
                hasSpokenNoWordMessage = false;
                incorrectAttempts = 0; // 틀린 시도 초기화
                totalExchanges = 0; // 총 교환 횟수 초기화
                lastExchange = { user: '', computer: '' }; // 마지막 교환 내용 초기화
                updateAttemptsDisplay();
                updateExchangeDisplay();
                showStatusMessage('게임이 재시작되었습니다.');
                // 페이지 새로 고침 (옵션)
                window.location.reload();
            })
            .catch((error) => {
                console.error('Error resetting game:', error);
                speakMessage('게임 재시작 중 오류가 발생했습니다.');
            });
    }

    /**
     * 게임 종료 및 메뉴로 돌아가기 함수
     */
    function quitGame() {
        speakMessage('게임을 종료하고 메뉴로 돌아갑니다.');
        window.location.href = "/word_chain_menu"; // 실제 메뉴 URL로 변경
    }

    /**
     * 게임 초기화 함수 호출
     * 게임을 처음 시작하거나 다시 시작할 때 서버 히스토리를 초기화
     */
    function initializeGame() {
        // 게임을 처음 시작하거나 다시 시작할 때 서버 히스토리를 초기화
        fetch('/word_chain/reset', { // 수정된 엔드포인트
            method: 'POST',
        })
            .then((response) => response.json())
            .then((data) => {
                console.log(data.message);
                initializeMenu();
            })
            .catch((error) => {
                console.error('Error resetting game:', error);
                speakMessage('게임 초기화 중 오류가 발생했습니다.');
                initializeMenu(); // 초기화 시도
            });
    }

    // 게임 초기화 호출
    initializeGame();

    // 브라우저가 로드될 때 폴링 시작 (점자 입력 처리)
    setInterval(fetchBrailleInput, 500); // 폴링 간격 500ms
});
