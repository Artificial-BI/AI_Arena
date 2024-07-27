// game_mode.js

// document.addEventListener('DOMContentLoaded', function() {
//     const modeButtons = document.querySelectorAll('.mode-btn');
//     const gameModeInput = document.getElementById('game_mode');
    
//     modeButtons.forEach(button => {
//         button.addEventListener('click', function() {
//             modeButtons.forEach(btn => btn.classList.remove('active'));
//             this.classList.add('active');
//             const selectedMode = this.dataset.mode;
            
//             fetch('/set_game_mode', {
//                 method: 'POST',
//                 headers: {
//                     'Content-Type': 'application/x-www-form-urlencoded'
//                 },
//                 body: new URLSearchParams({ 'game_mode': selectedMode })
//             }).then(response => {
//                 if (response.ok) {
//                     console.log('Game mode set to ' + selectedMode);
//                 } else {
//                     console.error('Failed to set game mode');
//                 }
//             });
//         });
//     });
// });

// Пример добавления нового функционала в существующие файлы JavaScript

// game_mode.js
// document.addEventListener('DOMContentLoaded', function() {
//     const modeButtons = document.querySelectorAll('.mode-btn');
//     const gameModeInput = document.getElementById('game_mode');
    
//     modeButtons.forEach(button => {
//         button.addEventListener('click', function() {
//             modeButtons.forEach(btn => btn.classList.remove('active'));
//             this.classList.add('active');
//             const selectedMode = this.dataset.mode;
            
//             fetch('/set_game_mode', {
//                 method: 'POST',
//                 headers: {
//                     'Content-Type': 'application/x-www-form-urlencoded'
//                 },
//                 body: new URLSearchParams({ 'game_mode': selectedMode })
//             }).then(response => {
//                 if (response.ok) {
//                     console.log('Game mode set to ' + selectedMode);
//                 } else {
//                     console.error('Failed to set game mode');
//                 }
//             });
//         });
//     });
// });
