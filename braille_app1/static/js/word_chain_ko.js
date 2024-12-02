// static/js/word_chain_ko.js

document.addEventListener('DOMContentLoaded', function () {
    let navigableItems;
    let currentIndex = 0;

    // 게임 상태 변수
    let incorrectAttempts = 0;
    let totalExchanges = 0;
    let lastExchange = { user: '', computer: '' };

    // 최신 입력 버퍼 및 번역된 텍스트 저장 변수
    let currentInputBuffer = [];
    let translatedText = '';

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

    /**
     * 번역된 텍스트를 화면에 표시하는 함수 (수정됨)
     * @param {string} translatedTextFromBackend - 백엔드에서 번역된 전체 텍스트
     * @param {number} cursorPosition - 커서 위치
     */
    function displayTranslatedInput(translatedTextFromBackend, cursorPosition) {
        const translatedWordDiv = document.getElementById('translated-word-ko');

        // 이전 내용 지우기
        translatedWordDiv.innerHTML = '';

        // 글로벌 변수에 번역된 텍스트 저장
        translatedText = translatedTextFromBackend;

        if (translatedText) {
            // 커서 위치에 따른 강조
            if (cursorPosition > 0 && cursorPosition <= translatedText.length) {
                const beforeCursor = translatedText.slice(0, cursorPosition - 1);
                const cursorChar = translatedText.charAt(cursorPosition - 1);
                const afterCursor = translatedText.slice(cursorPosition);

                // 커서 위치에 해당하는 문자 강조
                translatedWordDiv.innerHTML = `
                    ${beforeCursor}
                    <span class="cursor-highlight">${cursorChar}</span>
                    ${afterCursor}
                `;

                // 음성 피드백 추가
                speakMessage(cursorChar);
            } else {
                // 커서 위치가 유효하지 않으면 전체 텍스트 표시
                translatedWordDiv.innerText = translatedText;
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

                // 최신 입력 버퍼 저장
                currentInputBuffer = inputBuffer;

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

    /**
     * 번역된 텍스트를 백엔드로부터 받아오는 함수 (수정됨)
     * @param {Array} inputBuffer - 현재 입력된 점자 비트 리스트
     * @param {number} cursorPosition - 현재 커서 위치
     */
    function fetchTranslatedText(inputBuffer, cursorPosition) {
        console.log('Fetching translated text with input_buffer:', inputBuffer);
        fetch('/word_chain/translate_braille', { // 수정된 엔드포인트
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ input_buffer: inputBuffer }), // 입력 버퍼 전송
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
        console.log(`Translated Word before submission: "${translatedText}"`); // 디버깅 라인
        if (translatedText) {
            fetch('/word_chain/submit_braille_word', { // 수정된 엔드포인트
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ input_buffer: currentInputBuffer }), // 입력 버퍼 전송
            })
                .then(response => response.json())
                .then(data => {
                    // 번역된 단어 표시 영역 초기화
                    const translatedWordDiv = document.getElementById('translated-word-ko');
                    translatedWordDiv.innerHTML = '';

                    if (data.error) {
                        // 오류 메시지 표시 및 음성 피드백
                        document.getElementById('result-ko').innerText = data.error;
                        speakMessage(data.error);

                        // 단어 길이가 충분한 경우에만 틀린 시도 증가
                        const submittedWord = translatedText; // 번역된 텍스트 사용
                        if (submittedWord.length >= 2) {
                            incorrectAttempts += 1;
                            updateAttemptsDisplay();

                            if (incorrectAttempts >= 3) {
                                // 게임 종료 메시지 표시
                                showStatusMessage('게임 종료. 메뉴로 돌아가려면 메뉴로 돌아가기 버튼을 누르세요.');
                            }
                        }
                    } else {
                        // 성공 메시지 표시 및 음성 피드백
                        document.getElementById('result-ko').innerText = data.message;
                        speakMessage(`당신이 입력한 단어: ${translatedText}`);
                        lastExchange.user = translatedText;
                        updateExchangeDisplay();
                        totalExchanges += 1;
                        updateAttemptsDisplay();

                        if (data.computer_word) {
                            const computerWord = data.computer_word;
                            lastExchange.computer = computerWord;
                            updateExchangeDisplay();
                            speakMessage(`다음 단어: ${computerWord}`);
                            totalExchanges += 1;
                            updateAttemptsDisplay();
                        }

                        if (data.game_over) {
                            showStatusMessage('컴퓨터가 생성할 수 있는 단어가 없습니다. 메뉴로 돌아가려면 메뉴로 돌아가기 버튼을 누르세요.');
                        }
                    }
                })
                .catch(error => {
                    console.error('Error submitting Braille word:', error);
                    speakMessage('오류가 발생했습니다.');
                });
        } else {
            speakMessage('제출할 단어가 없습니다.');
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
