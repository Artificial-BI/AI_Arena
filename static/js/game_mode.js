// game_mode.js

document.addEventListener('DOMContentLoaded', function() {
    const modeButtons = document.querySelectorAll('.mode-btn');
    const gameModeInput = document.getElementById('game_mode');
    
    modeButtons.forEach(button => {
        button.addEventListener('click', function() {
            modeButtons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');
            gameModeInput.value = this.dataset.mode;
        });
    });
});
