/**
 * 运势数据与抽签逻辑
 */

// 运势等级配置（按概率分布）
const fortuneLevels = [
    { name: '大吉', probability: 0.05, color: '#FFD700' },  // 5% 金色
    { name: '吉', probability: 0.15, color: '#50C878' },    // 15% 绿色
    { name: '中吉', probability: 0.20, color: '#4ECDC4' },  // 20% 青色
    { name: '小吉', probability: 0.25, color: '#45B7D1' },  // 25% 蓝色
    { name: '末吉', probability: 0.20, color: '#96CEB4' },  // 20% 浅绿
    { name: '凶', probability: 0.15, color: '#FF6B6B' }     // 15% 红色
];

// 签文库（30条，分配到各运势等级）
const fortuneTexts = {
    '大吉': [
        '今日运势极佳，诸事皆宜。保持这份好心情，好运自会连连。',
        '天赐良机，势不可挡。放手去做，成功就在眼前。',
        '吉星高照，万事如意。把握当下，未来可期。',
        '贵人相助，逢凶化吉。你的善良正在为你积累福报。',
        '今日宜开创新篇章，你的努力必将收获丰硕的果实。'
    ],
    '吉': [
        '整体运势良好，稳步前进。保持耐心，好事将至。',
        '付出终有回报，坚持下去就会看到曙光。',
        '今天适合与人为善，你的真诚会得到回应。',
        '机遇与挑战并存，把握好节奏即可顺利度过。',
        '保持积极心态，好运自然会降临到你身边。'
    ],
    '中吉': [
        '运势平稳，凡事三思而后行必有收获。',
        '今日宜静心养性，不宜冒进，稳中求胜为上策。',
        '平平稳稳才是真，保持平常心对待得失。',
        '循序渐进，步步为营，好运藏在细节里。',
        '今日适合回顾过去，总结经验再出发。',
        '顺其自然不强求，是你的终将会到来。'
    ],
    '小吉': [
        '运势小有波折，但终会化险为夷，不必过于担忧。',
        '今天可能会有小惊喜，保持期待之心吧。',
        '看似平常的一天，也许隐藏着小小的幸运。',
        '今日宜保守行事，不宜做重大决定。',
        '保持乐观，小的顺利会累积成大的成就。'
    ],
    '末吉': [
        '运势稍显低迷，但不必气馁，静待转机。',
        '今日宜修身养性，多行善事积累福报。',
        '可能会遇到一些小麻烦，保持平和心态即可化解。',
        '凡事不可强求，顺势而为才是明智之举。',
        '困难只是暂时的，坚持下去就会看到希望。'
    ],
    '凶': [
        '今日运势不佳，宜谨言慎行，避免与人发生冲突。',
        '运势较低迷，宜静不宜动，多做准备以应对变化。',
        '今日可能会遇到一些挫折，但请相信雨后总会天晴。',
        '保持低调，避免锋芒毕露，韬光养晦等待时机。'
    ]
};

/**
 * 根据概率分布随机抽取运势
 * @returns {Object} 运势对象，包含name和color
 */
function drawFortune() {
    const rand = Math.random();
    let cumulative = 0;
    for (const level of fortuneLevels) {
        cumulative += level.probability;
        if (rand < cumulative) {
            return level;
        }
    }
    return fortuneLevels[fortuneLevels.length - 1];
}

/**
 * 根据运势等级获取随机签文
 * @param {string} fortuneName 运势等级名称
 * @returns {string} 签文内容
 */
function getFortuneText(fortuneName) {
    const texts = fortuneTexts[fortuneName];
    if (!texts || texts.length === 0) {
        return '今日暂无签文，请保持心诚。';
    }
    const randomIndex = Math.floor(Math.random() * texts.length);
    return texts[randomIndex];
}

/**
 * 生成幸运数字 (1-9)
 * @returns {number} 幸运数字
 */
function getLuckyNumber() {
    return Math.floor(Math.random() * 9) + 1;
}

/**
 * 执行完整的抽签流程
 * @returns {Object} 抽签结果对象
 */
function draw() {
    const fortune = drawFortune();
    const text = getFortuneText(fortune.name);
    const luckyNumber = getLuckyNumber();

    return {
        fortune: fortune,
        text: text,
        luckyNumber: luckyNumber
    };
}