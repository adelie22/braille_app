// static/js/word_chain_en.js

document.addEventListener('DOMContentLoaded', function () {
    let navigableItems;
    let currentIndex = 0;
    let isComposing = false;

    // 게임 상태 변수
    let incorrectAttempts = 0;
    let totalExchanges = 0;
    let lastExchange = { user: '', computer: '' };
    let gameOver = false;

    // 초기화 함수
    function initializeMenu() {
        navigableItems = [
            document.getElementById('user-word-ko'),
            document.getElementById('back-to-menu-ko'),
        ];

        currentIndex = 0;
        navigableItems[currentIndex].classList.add('selected');
        navigableItems[currentIndex].focus();
        speakMessage(getItemLabel(navigableItems[currentIndex]));
        updateAttemptsDisplay();
        updateExchangeDisplay();
    }

    // 음성 출력 함수
    function speakMessage(message) {
        console.log('Speaking message:', message); // 디버깅 로그
        window.speechSynthesis.cancel(); // 이전 음성 중단
        setTimeout(() => {
            const utterance = new SpeechSynthesisUtterance(message);
            utterance.lang = 'ko-KR';
            window.speechSynthesis.speak(utterance);
        }, 100); // 지연 시간 추가
    }

    // 각 항목의 라벨 가져오기
    function getItemLabel(item) {
        if (item.tagName === 'INPUT') {
            return '단어 입력창';
        } else if (item.id === 'back-to-menu-ko') {
            return '뒤로가기 버튼';
        } else if (item.id === 'retry-button-ko') {
            return '재시도 버튼';
        } else if (item.id === 'cancel-button-ko') {
            return '취소 버튼';
        }
        return '';
    }

    // 시도 횟수 및 교환 횟수 업데이트 함수
    function updateAttemptsDisplay() {
        const attemptsDisplay = document.getElementById('attempts-ko');
        attemptsDisplay.innerText = `틀린 횟수: ${incorrectAttempts} | 주고 받은 횟수: ${totalExchanges}`;
    }

    // 교환 내용 업데이트 함수
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

            // 단어 애니메이션
            exchangeElement.style.transform = 'scale(1.2)';
            exchangeElement.style.opacity = 1; // 새로운 단어 보여주기
            setTimeout(() => {
                exchangeElement.style.transform = 'scale(1)'; // 크기를 원래대로
            }, 300);
        }, 300);
    }



    // 교환 내용 업데이트 함수 (단어를 직접 교환할 때 사용)
    function updateExchange(userWord, computerWord) {
        const exchangeElement = document.getElementById('exchange-ko');
        exchangeElement.style.opacity = 0; // 기존 단어 숨기기

        setTimeout(() => {
            if (userWord && computerWord) {
                exchangeElement.innerHTML = `${userWord} → ${computerWord}`;
            } else if (userWord) {
                exchangeElement.innerHTML = `${userWord} → `;
            } else if (computerWord) {
                exchangeElement.innerHTML = `→ ${computerWord}`;
            } else {
                exchangeElement.innerHTML = '';
            }

            // 게임스러운 애니메이션 추가
            exchangeElement.style.transform = 'scale(1.5)';
            exchangeElement.style.transition = 'transform 0.3s ease, opacity 0.3s ease';
            exchangeElement.style.opacity = 1; // 새로운 단어 보여주기
            setTimeout(() => {
                exchangeElement.style.transform = 'scale(1)'; // 크기를 원래대로
            }, 300);
        }, 300);
    }

    // 메뉴 간 이동 함수
    function navigateMenu(direction) {
        navigableItems[currentIndex].classList.remove('selected');
        window.speechSynthesis.cancel(); // 현재 음성 중단

        // 인덱스 업데이트
        if (direction === 'left') {
            currentIndex = (currentIndex - 1 + navigableItems.length) % navigableItems.length;
        } else if (direction === 'right') {
            currentIndex = (currentIndex + 1) % navigableItems.length;
        }

        navigableItems[currentIndex].classList.add('selected');
        navigableItems[currentIndex].focus();
        speakMessage(getItemLabel(navigableItems[currentIndex]));
    }
    
    document.addEventListener('keydown', (event) => {
        if (document.getElementById('popup-ko').style.display === 'block') {
            // 팝업이 열려있을 때는 외부 키보드 이벤트 무시
            return;
        }

        if (gameOver) {
            // 게임 종료 상태에서는 키보드 입력 무시
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
            if (activeElement.id === 'back-to-menu-ko') {
                // 뒤로가기 버튼 클릭 동작
                window.location.href = "/word_chain_menu"; // 실제 메뉴 URL로 변경하세요
            }
        }
    });

    //// 한국어는 조합 중 엔터 두 번 입력되는 이벤트 발생하므로 영어와 다르게 입력코드를 아래와 같이 작성 ////
    // 조합 시작 이벤트
    document.getElementById('user-word-ko').addEventListener('compositionstart', () => {
        isComposing = true; // 조합 중 상태로 설정
    });

    // 조합 종료 이벤트
    document.getElementById('user-word-ko').addEventListener('compositionend', () => {
        isComposing = false; // 조합 완료 상태로 설정
    });

    // 키다운 이벤트
    document.getElementById('user-word-ko').addEventListener('keydown', (event) => {
        if (event.key === 'Enter' && !isComposing) { // 조합 중이 아닐 때만 처리
            const word = event.target.value.trim(); // 현재 입력된 단어 가져오기
            if (word) {
                submitWord(word); // 단어 제출 함수 호출
            } else {
                speakMessage('단어를 입력하세요.');
            }
            event.preventDefault(); // 기본 Enter 동작 방지
        }
    });




    // 사용자가 단어를 제출했을 때
    function submitWord(word) {
        // 단어 길이 확인 (3글자 미만이면 틀린 횟수 증가하지 않음)
        const isKorean = /^[가-힣ㄱ-ㅎㅏ-ㅣ]+$/.test(word); // 한글 음절, 자음, 모음 허용// 한국어만 허용하는 정규식
        if (!isKorean) {
            speakMessage('단어를 한국어로 입력하세요.');
            document.getElementById('user-word-ko').value = ''; // 입력창 초기화
            document.getElementById('user-word-ko').focus(); // 입력창에 다시 포커스
            return; // 더 이상 처리하지 않음
        }


        // 단어 길이 확인 (3글자 미만이면 틀린 횟수 증가하지 않음)
        if (word.length < 2) {
            speakMessage('두 글자 이상 입력하세요.');
            document.getElementById('user-word-ko').value = ''; // 입력창 초기화
            document.getElementById('user-word-ko').focus(); // 입력창에 다시 포커스
            return; // 더 이상 처리하지 않음
        }

        fetch('/word_chain/check_word', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ word: word }),
            // 1회차 수정 오류시 JSON타입으로 받아오는지 확인해보기
        })
            .then((response) => response.json())
            .then((data) => {
                // 입력창 초기화 및 포커스는 성공/실패에 관계없이 항상 수행
                document.getElementById('user-word-ko').value = ''; // 입력창 초기화
                document.getElementById('user-word-ko').focus(); // 입력창에 다시 포커스

                if (data.error) {
                    document.getElementById('result-ko').innerText = data.error;
                    speakMessage(data.error);

                    // 틀린 횟수 증가 조건 추가: 3단어 이상인 경우에만 증가
                    if (word.length >= 2) {
                        incorrectAttempts += 1; // 틀린 횟수 증가
                        updateAttemptsDisplay(); // 틀린 횟수 업데이트

                        if (incorrectAttempts >= 3) {
                            gameOver = true;
                            speakMessage('게임 종료. 다시하려면 재시도, 종료하려면 취소 버튼을 누르세요');
                            openGameOverPopup();
                        }
                    }
                } else {
                    document.getElementById('result-ko').innerText = data.message;
                    speakMessage(word); // 사용자 단어 음성 출력
                    lastExchange.user = word; // 사용자 단어 기록
                    updateExchangeDisplay(); // 교환 내용 업데이트
                    totalExchanges += 1; // 교환 횟수 증가
                    updateAttemptsDisplay(); // 교환 횟수 업데이트

                    fetch('/word_chain/generate_word')
                        .then((response) => response.json())
                        .then((computerData) => {
                            if (computerData.error) {
                                speakMessage(computerData.error);
                                gameOver = true;
                                speakMessage('컴퓨터가 생성할 수 있는 단어가 없습니다. 다시하려면 재시도, 종료하려면 취소 버튼을 누르세요');
                                openGameOverPopup();
                            } else {
                                const computerWord = computerData.word;
                                lastExchange.computer = computerWord; // 컴퓨터 단어 기록
                                updateExchangeDisplay(); // 교환 내용 업데이트
                                speakMessage(computerWord); // 컴퓨터 단어 음성 출력
                                totalExchanges += 1; // 교환 횟수 증가
                                updateAttemptsDisplay(); // 교환 횟수 업데이트
                            }
                        });
                }
            })
            .catch((error) => {
                console.error('Error:', error);
                speakMessage('An error occurred.');

                // 입력창 초기화 및 포커스는 실패 시에도 수행
                document.getElementById('user-word-ko').value = '';
                document.getElementById('user-word-ko').focus();
            });
    }




    // // 유효하지 않은 단어 처리 함수
    // function handleInvalidWord(errorMessage, word) {
    //     console.log(`Invalid word: ${errorMessage}`);
    //     speakMessage(errorMessage);
    //     incorrectAttempts += 1;
    //     updateAttemptsDisplay();

    //     // 1번 기능: 3글자 미만 입력 시
    //     if (errorMessage.includes('at least')) {
    //         // 이미 음성으로 안내되었으므로 추가 동작 필요 없음
    //     }

    //     // 3번 기능: 올바르지 않은 시작 글자
    //     // 4번 기능: 중복 단어
    //     // 이 두 기능은 errorMessage에 따라 분기 처리됨

    //     // 6번 기능: 3번 틀리면 게임 종료
    //     if (incorrectAttempts >= 3) {
    //         gameOver = true;
    //         speakMessage('게임 종료. 다시하려면 재시도, 종료하려면 취소 버튼을 누르세요');
    //         openGameOverPopup();
    //     }
    // }

    // 유효한 단어 처리 함수
    function handleValidWord(userWord, history) {
        console.log(`Valid word: ${userWord}`);
        speakMessage(`You entered: ${userWord}`);
        document.getElementById('user-word-ko').value = '';
        totalExchanges += 1;
        updateAttemptsDisplay();
        lastExchange.user = userWord;
        updateExchangeDisplay();

        // 컴퓨터 단어 생성
        generateComputerWord();
    }

    // 컴퓨터 단어 생성 함수
    function generateComputerWord() { 
        //1회차 수정 이후 오류 시 generate_word로 json 제대로 받아오는지 확인 필요
        fetch('/word_chain/generate_word', {
            method: 'GET',
        })
            .then((response) => response.json())
            .then((data) => {
                if (data.error) {
                    handleComputerError(data.error);
                } else {
                    handleComputerWord(data.word);
                }
            })
            .catch((error) => {
                console.error('Error:', error);
                speakMessage('단어 생성 중 오류가 발생했습니다.');
            });
    }

    // 컴퓨터 단어 처리 함수
    function handleComputerWord(computerWord) {
        console.log(`Computer generated: ${computerWord}`);
        speakMessage(`Computer entered: ${computerWord}`);
        lastExchange.computer = computerWord;
        updateExchangeDisplay();
        totalExchanges += 1;
        updateAttemptsDisplay();
    }

    // 컴퓨터 오류 처리 함수
    function handleComputerError(errorMessage) {
        console.log(`Computer error: ${errorMessage}`);
        speakMessage(errorMessage);
        gameOver = true;
        speakMessage('컴퓨터가 생성할 수 있는 단어가 없습니다. 다시하려면 재시도, 종료하려면 취소 버튼을 누르세요.');
        openGameOverPopup();
    }

    // 히스토리 업데이트 함수
    function updateHistory(history) {
        const historyList = document.getElementById('history-ko');
        historyList.innerHTML = '';
        history.forEach((word) => {
            const listItem = document.createElement('li');
            listItem.textContent = word;
            historyList.appendChild(listItem);
        });
    }

    // 팝업 열기 함수
    function openGameOverPopup() {
        const popup = document.getElementById('popup-ko');
        const message = document.getElementById('popup-message-ko');

        if (incorrectAttempts >= 3) {
            message.innerText = '게임 종료.  다시하려면 재시도, 종료하려면 취소 버튼을 누르세요.';
        } else {
            message.innerText = '컴퓨터가 생성할 수 있는 단어가 없습니다. 다시하려면 재시도, 종료하려면 취소 버튼을 누르세요.';
        }

        popup.style.display = 'block';
        navigableItems = [
            document.getElementById('retry-button-ko'),
            document.getElementById('cancel-button-ko'),
        ];
        currentIndex = 0;
        navigableItems[currentIndex].classList.add('selected');
        navigableItems[currentIndex].focus();
        speakMessage(getItemLabel(navigableItems[currentIndex]));
    }

    // 팝업 닫기 함수
    function closeGameOverPopup() {
        const popup = document.getElementById('popup-ko');
        popup.style.display = 'none';
        navigableItems.forEach(item => item.classList.remove('selected'));
        currentIndex = 0;
        initializeMenu();
    }

    // 팝업 내 키 입력 핸들러
    function handlePopupNavigationKo(e) {
        e.preventDefault();
        if (!navigableItems) return;

        if (e.key === 'ArrowLeft') {
            navigatePopupKo('left');
        } else if (e.key === 'ArrowRight') {
            navigatePopupKo('right');
        } else if (e.key === 'Enter') {
            const activeElement = navigableItems[currentIndex];
            if (activeElement.id === 'retry-button-ko') {
                // 게임 재시작 버튼 클릭 동작
                restartGame();
            } else if (activeElement.id === 'cancel-button-ko') {
                // 게임 종료 버튼 클릭 동작
                quitGame();
            }
        } else if (e.key === 'Escape') {
            // ESC 키를 누르면 게임 종료
            quitGame();
        }
    }

    // 팝업 메뉴 간 이동 함수
    function navigatePopupKo(direction) {
        navigableItems[currentIndex].classList.remove('selected');
        window.speechSynthesis.cancel(); // 현재 음성 중단

        // 인덱스 업데이트
        if (direction === 'left') {
            currentIndex = (currentIndex - 1 + navigableItems.length) % navigableItems.length;
        } else if (direction === 'right') {
            currentIndex = (currentIndex + 1) % navigableItems.length;
        }

        navigableItems[currentIndex].classList.add('selected');
        navigableItems[currentIndex].focus();
        speakMessage(getItemLabel(navigableItems[currentIndex]));
    }

    // 팝업 이벤트 리스너 추가
    document.addEventListener('keydown', (event) => {
        if (document.getElementById('popup-ko').style.display === 'block') {
            if (event.key === 'ArrowLeft' || event.key === 'ArrowRight' || event.key === 'Enter' || event.key === 'Escape') {
                handlePopupNavigationKo(event);
            }
        }
    });

    // 팝업 버튼 클릭 이벤트 리스너
    document.getElementById('retry-button-ko').addEventListener('click', () => {
        restartGame();
    });

    document.getElementById('cancel-button-ko').addEventListener('click', () => {
        quitGame();
    });

    // 게임 재시작 함수
    function restartGame() {
        fetch('/word_chain/reset', {
            method: 'POST',
        })
            .then((response) => response.json())
            .then((data) => {
                console.log(data.message);
                speakMessage('게임이 종료되었습니다.');
                incorrectAttempts = 0; // 틀린 횟수 초기화
                totalExchanges = 0; // 교환 횟수 초기화
                lastExchange = { user: '', computer: '' }; // 교환 내용 초기화
                updateAttemptsDisplay(); // 시도 횟수 표시 초기화
                updateExchangeDisplay(); // 교환 내용 표시 초기화
                closeGameOverPopup();
                // 페이지 새로 고침
                window.location.reload();
            })
            .catch((error) => {
                console.error('Error resetting game:', error);
            });
    }

    // 게임 종료 함수
    function quitGame() {
        speakMessage('게임 종료. 메뉴로 돌아갑니다.');
        window.location.href = "/word_chain_menu"; // 실제 메뉴 URL로 변경하세요
    }

    // 게임 초기화 함수 호출
    function initializeGame() {
        // 게임을 처음 시작하거나 다시 시작할 때 서버 히스토리를 초기화
        fetch('/word_chain/reset', {
            method: 'POST',
        })
            .then((response) => response.json())
            .then((data) => {
                console.log(data.message);
                initializeMenu();
            })
            .catch((error) => {
                console.error('Error resetting game:', error);
                initializeMenu(); // 초기화 시도
            });
    }



    // 게임 초기화 호출
    initializeGame();
});
