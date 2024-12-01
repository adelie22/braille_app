// static/js/word_chain_ko.js

document.addEventListener('DOMContentLoaded', function () {
    let navigableItems;
    let currentIndex = 0;

    // 게임 상태 변수
    let incorrectAttempts = 0;
    let totalExchanges = 0;
    let lastExchange = { user: '', computer: '' };
    // 게임 종료 플래그 제거

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
        if (item.tagName === 'DIV') {
            return '번역된 단어';
        } else if (item.id === 'back-to-menu-ko') {
            return '메뉴로 돌아가기 버튼';
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

    // 번역된 단어 표시 함수 (수정됨)
    function displayTranslatedInput(translatedSyllables, cursorPosition) {
        const translatedWordDiv = document.getElementById('translated-word-ko');

        // 이전 내용 지우기
        translatedWordDiv.innerHTML = '';

        // 번역된 음절 리스트를 순차적으로 화면에 추가
        translatedSyllables.forEach((syllable, index) => {
            const syllableSpan = document.createElement('span');
            syllableSpan.textContent = syllable;

            // 마지막 음절에만 커서 강조 추가
            if (index === translatedSyllables.length - 1) {
                const cursorHighlight = document.createElement('span');
                cursorHighlight.classList.add('cursor-highlight');
                cursorHighlight.textContent = syllable; // 현재 음절을 강조
                syllableSpan.innerHTML = ''; // 기존 텍스트 제거
                syllableSpan.appendChild(cursorHighlight);

                // 음성 피드백 추가
                speakMessage(syllable);
            }

            translatedWordDiv.appendChild(syllableSpan);
        });
    }

    // 상태 메시지 표시 및 음성 출력 함수
    function showStatusMessage(message) {
        const statusMessageDiv = document.getElementById('status-message-ko');
        if (statusMessageDiv) {
            statusMessageDiv.innerText = message;
            speakMessage(message);
        }
    }

    // 점자 입력 및 컨트롤 신호 폴링 함수
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

                // 입력이 있는 경우 번역된 텍스트 표시
                if (inputBuffer && inputBuffer.length > 0) {
                    fetchTranslatedText(inputBuffer, cursorPosition);
                } else {
                    displayTranslatedInput([], cursorPosition); // 입력이 없으면 표시 지우기
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
                // 메뉴로 돌아가기
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

    // 번역된 텍스트를 백엔드로부터 받아오는 함수 (수정됨)
    function fetchTranslatedText(inputBuffer, cursorPosition) {
        fetch('/word_chain/translate_braille', { // 수정된 엔드포인트
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ input_buffer: inputBuffer }), // 필요 시 데이터 추가
        })
            .then(response => response.json())
            .then(data => {
                if (data.translated_syllables !== undefined && data.cursor_position !== undefined) {
                    displayTranslatedInput(data.translated_syllables, data.cursor_position);
                }
            })
            .catch(error => console.error('Error translating Braille input:', error));
    }

    // 점자 단어 제출 함수
    function submitBrailleWord() {
        const translatedWordDiv = document.getElementById('translated-word-ko');
        let translatedWord = translatedWordDiv.textContent || translatedWordDiv.innerText || '';

        // 불필요한 공백 및 줄바꿈 문자 제거
        translatedWord = translatedWord.replace(/\u00A0/g, '').replace(/[\r\n]+/g, '').trim();

        console.log(`Translated Word before submission: "${translatedWord}"`); // 디버깅 라인
        if (translatedWord) {
            fetch('/word_chain/submit_braille_word', { // 수정된 엔드포인트
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({}), // 필요 시 데이터 추가
            })
                .then(response => response.json())
                .then(data => {
                    // 번역된 단어 표시 영역 초기화
                    const translatedWordDiv = document.getElementById('translated-word-ko');
                    translatedWordDiv.innerHTML = '';

                    if (data.error) {
                        document.getElementById('result-ko').innerText = data.error;
                        speakMessage(data.error);

                        // 단어 길이가 충분한 경우에만 틀린 시도 증가
                        if (translatedWord.length >= 2) {
                            incorrectAttempts += 1;
                            updateAttemptsDisplay();

                            if (incorrectAttempts >= 3) {
                                // 게임 종료 메시지 표시
                                showStatusMessage('게임 종료. 메뉴로 돌아가려면 메뉴로 돌아가기 버튼을 누르세요.');
                            }
                        }
                    } else {
                        document.getElementById('result-ko').innerText = data.message;
                        speakMessage(`당신이 입력한 단어: ${translatedWord}`);
                        lastExchange.user = translatedWord;
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

    // 게임 재시작 함수
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

    // 게임 종료 및 메뉴로 돌아가기 함수
    function quitGame() {
        speakMessage('게임을 종료하고 메뉴로 돌아갑니다.');
        window.location.href = "/word_chain_menu"; // 실제 메뉴 URL로 변경
    }

    // 게임 초기화 함수 호출
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

    // 'Back to Menu' 버튼 클릭 이벤트 리스너 추가
    document.getElementById('back-to-menu-ko').addEventListener('click', () => {
        quitGame();
    });

    // 브라우저가 로드될 때 폴링 시작 (점자 입력 처리)
    setInterval(fetchBrailleInput, 500); // 폴링 간격 500ms
    // 게임 초기화 호출
    initializeGame();
});
