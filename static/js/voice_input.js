// --- voice_input.js ---
// document.addEventListener('DOMContentLoaded', function() {
//     const voiceInputBtn = document.getElementById('voice-input-btn');
//     const descriptionField = document.getElementById('description');

//     if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
//         console.log('Speech Recognition API is supported in this browser.');

//         const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
//         const recognition = new SpeechRecognition();

//         recognition.continuous = false;
//         recognition.interimResults = false;
//         recognition.lang = 'ru-RU';

//         recognition.onstart = function() {
//             console.log('Voice recognition started.');
//             voiceInputBtn.textContent = 'Говорите...';
//             voiceInputBtn.disabled = true;
//         };

//         recognition.onresult = function(event) {
//             console.log('Voice recognition result received.');
//             if (event.results.length > 0) {
//                 const transcript = event.results[0][0].transcript;
//                 console.log('Transcript:', transcript);
//                 descriptionField.value += transcript + ' ';
//             } else {
//                 console.log('No results received.');
//             }
//             voiceInputBtn.textContent = 'Нажмите и говорите';
//             voiceInputBtn.disabled = false;
//         };

//         recognition.onerror = function(event) {
//             console.error('Voice recognition error:', event.error);
//             voiceInputBtn.textContent = 'Нажмите и говорите';
//             voiceInputBtn.disabled = false;
//         };

//         recognition.onend = function() {
//             console.log('Voice recognition ended.');
//             voiceInputBtn.textContent = 'Нажмите и говорите';
//             voiceInputBtn.disabled = false;
//         };

//         voiceInputBtn.addEventListener('click', function() {
//             console.log('Voice input button clicked.');
//             recognition.start();
//         });
//     } else {
//         console.error('Speech Recognition API is not supported in this browser.');
//         voiceInputBtn.disabled = true;
//         voiceInputBtn.textContent = 'Голосовой ввод не поддерживается';
//     }
// });
