/**
 * 抽签应用主逻辑
 */

document.addEventListener('DOMContentLoaded', function() {
    // 获取页面元素
    const drawBtn = document.getElementById('drawBtn');
    const result = document.getElementById('result');
    const fortuneCard = document.getElementById('fortuneCard');
    const cardFront = document.getElementById('cardFront');
    const cardBack = document.getElementById('cardBack');
    const fortuneRank = document.getElementById('fortuneRank');
    const fortuneText = document.getElementById('fortuneText');
    const luckyNumber = document.getElementById('luckyNumber');

    let hasDrawn = false;

    drawBtn.addEventListener('click', function() {
        if (hasDrawn) {
            resetFortune();
        } else {
            drawFortuneAndShow();
        }
    });

    function drawFortuneAndShow() {
        result.style.display = 'block';
        drawBtn.disabled = true;
        drawBtn.textContent = '占卜中...';

        cardFront.style.display = 'flex';
        cardBack.style.display = 'none';
        fortuneCard.classList.remove('flipping');

        setTimeout(function() {
            const resultData = draw();

            fortuneRank.textContent = resultData.fortune.name;
            fortuneRank.style.color = resultData.fortune.color;
            fortuneText.textContent = resultData.text;
            luckyNumber.textContent = resultData.luckyNumber;

            cardFront.style.display = 'none';
            cardBack.style.display = 'flex';
            fortuneCard.classList.add('flipping');

            drawBtn.textContent = '重新抽签';
            drawBtn.disabled = false;
            hasDrawn = true;
        }, 1500);
    }

    function resetFortune() {
        fortuneCard.classList.remove('flipping');
        drawBtn.disabled = true;
        drawBtn.textContent = '占卜中...';

        setTimeout(function() {
            const resultData = draw();

            fortuneRank.textContent = resultData.fortune.name;
            fortuneRank.style.color = resultData.fortune.color;
            fortuneText.textContent = resultData.text;
            luckyNumber.textContent = resultData.luckyNumber;

            cardFront.style.display = 'none';
            cardBack.style.display = 'flex';

            setTimeout(function() {
                fortuneCard.classList.add('flipping');
                drawBtn.textContent = '重新抽签';
                drawBtn.disabled = false;
            }, 100);

        }, 600);
    }
});