import os
import pymysql
from flask import Flask, render_template_string, request, jsonify

app = Flask(__name__)

# ─────────────────────────────────────────────────────────────────
# DATABASE CONNECTION
# Values come from ECS Task Definition → Environment Variables
# NEVER hardcode passwords! Use env variables ✅ (DevOps best practice)
# ─────────────────────────────────────────────────────────────────
def get_db_connection():
    return pymysql.connect(
        host=os.environ["DB_HOST"],         # RDS endpoint
        user=os.environ["DB_USER"],         # e.g. admin
        password=os.environ["DB_PASSWORD"], # from Secrets Manager or ECS env
        database=os.environ["DB_NAME"],     # e.g. bookdb
        cursorclass=pymysql.cursors.DictCursor,
        connect_timeout=5
    )

# ─────────────────────────────────────────────────────────────────
# AUTO-CREATE TABLE ON STARTUP
# Runs once when the container starts
# ─────────────────────────────────────────────────────────────────
def init_db():
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS reviews (
                    id         INT AUTO_INCREMENT PRIMARY KEY,
                    name       VARCHAR(100)  NOT NULL,
                    email      VARCHAR(150)  NOT NULL,
                    message    TEXT          NOT NULL,
                    created_at TIMESTAMP     DEFAULT CURRENT_TIMESTAMP
                )
            """)
        conn.commit()
        conn.close()
        print("✅ Database table ready.")
    except Exception as e:
        print(f"⚠️  DB init warning: {e}")

# ─────────────────────────────────────────────────────────────────
# BOOK DATA
# ─────────────────────────────────────────────────────────────────
BOOKS = [
    {
        "title": "To Kill a Mockingbird", "emoji": "⚖️", "genre": "Classic Fiction",
        "year": "1960", "author": "Harper Lee", "pages": "281",
        "tagline": "A Story of Racial Injustice and Moral Growth",
        "bio": "Set in the American South during the 1930s, this Pulitzer Prize-winning novel follows young Scout Finch as her father Atticus defends a Black man unjustly accused of a crime. A profound exploration of racial injustice, class, and human dignity through the innocent eyes of a child.",
        "known_for": ["Pulitzer Prize 1961", "Atticus Finch", "American Classic"],
    },
    {
        "title": "1984", "emoji": "👁️", "genre": "Dystopian",
        "year": "1949", "author": "George Orwell", "pages": "328",
        "tagline": "Big Brother Is Watching You",
        "bio": "George Orwell's chilling vision of a totalitarian future where the government controls all information, rewrites history, and surveils every citizen. Winston Smith's desperate struggle against the Party gave the world concepts like doublethink, thoughtcrime, and the memory hole.",
        "known_for": ["Big Brother", "Newspeak", "Dystopian Masterpiece"],
    },
    {
        "title": "The Great Gatsby", "emoji": "🥂", "genre": "Classic Fiction",
        "year": "1925", "author": "F. Scott Fitzgerald", "pages": "180",
        "tagline": "A Glittering Tale of the American Dream",
        "bio": "Set in the roaring 1920s, Fitzgerald's masterpiece explores themes of wealth, class, love, and the hollowness of the American Dream through the tragic story of the mysterious millionaire Jay Gatsby and his obsession with the beautiful Daisy Buchanan.",
        "known_for": ["American Dream", "Jazz Age", "Literary Classic"],
    },
    {
        "title": "Dune", "emoji": "🏜️", "genre": "Science Fiction",
        "year": "1965", "author": "Frank Herbert", "pages": "688",
        "tagline": "The Greatest Science Fiction Novel Ever Written",
        "bio": "Set in a distant future where noble houses control planets, Dune follows Paul Atreides on the desert world Arrakis, the only source of the universe's most valuable substance. An epic saga of politics, religion, ecology, and destiny that changed science fiction forever.",
        "known_for": ["Spice Melange", "Hugo & Nebula Awards", "Sci-Fi Epic"],
    },
    {
        "title": "Pride and Prejudice", "emoji": "💌", "genre": "Romance",
        "year": "1813", "author": "Jane Austen", "pages": "432",
        "tagline": "A Timeless Comedy of Manners and Matrimony",
        "bio": "Jane Austen's witty and beloved novel follows the five Bennet sisters as they navigate love, marriage, and society in Regency-era England. The sparkling romance between the headstrong Elizabeth Bennet and the proud Mr. Darcy remains one of literature's greatest love stories.",
        "known_for": ["Mr. Darcy", "Regency Romance", "Austen Masterpiece"],
    },
    {
        "title": "The Hitchhiker's Guide to the Galaxy", "emoji": "🌌", "genre": "Science Fiction",
        "year": "1979", "author": "Douglas Adams", "pages": "193",
        "tagline": "Don't Panic",
        "bio": "After Earth is demolished to make way for a hyperspace bypass, Arthur Dent is whisked across the universe by his alien friend Ford Prefect. Adams' comic masterpiece blends absurdist humor with surprisingly deep philosophical musings. The answer to life, the universe, and everything is 42.",
        "known_for": ["The Answer is 42", "Towels in Space", "British Sci-Fi Comedy"],
    },
    {
        "title": "The Alchemist", "emoji": "✨", "genre": "Philosophical Fiction",
        "year": "1988", "author": "Paulo Coelho", "pages": "208",
        "tagline": "Follow Your Personal Legend",
        "bio": "Paulo Coelho's beloved fable follows Santiago, an Andalusian shepherd boy who travels from Spain to Egypt in search of treasure. Along the way he learns profound lessons about listening to your heart, recognizing opportunity, and following your personal legend.",
        "known_for": ["Personal Legend", "Soul of the World", "65M+ Copies Sold"],
    },
    {
        "title": "Crime and Punishment", "emoji": "🗡️", "genre": "Psychological Fiction",
        "year": "1866", "author": "Fyodor Dostoevsky", "pages": "550",
        "tagline": "The Psychology of Guilt and Redemption",
        "bio": "Dostoevsky's psychological masterpiece follows Rodion Raskolnikov, a destitute student who commits a murder believing himself to be above moral law. The novel's unflinching exploration of guilt, isolation, and redemption established Dostoevsky as one of the greatest writers who ever lived.",
        "known_for": ["Russian Literature", "Psychological Depth", "Literary Masterpiece"],
    },
    {
        "title": "The Hobbit", "emoji": "🏔️", "genre": "Fantasy",
        "year": "1937", "author": "J.R.R. Tolkien", "pages": "310",
        "tagline": "There and Back Again",
        "bio": "Tolkien's enchanting prequel to The Lord of the Rings follows the reluctant Bilbo Baggins on a grand adventure with a company of dwarves and the wizard Gandalf. A timeless tale of courage, friendship, and the discovery of unexpected heroism that created the modern fantasy genre.",
        "known_for": ["Middle-Earth", "Bilbo & Gandalf", "Father of Modern Fantasy"],
    },
    {
        "title": "One Hundred Years of Solitude", "emoji": "🦋", "genre": "Magical Realism",
        "year": "1967", "author": "Gabriel García Márquez", "pages": "417",
        "tagline": "The Story of the Buendía Family",
        "bio": "García Márquez's Nobel Prize-winning masterpiece chronicles seven generations of the Buendía family in the fictional town of Macondo. Weaving together reality and fantasy with lyrical prose, it is considered the pinnacle of magical realism and one of the greatest novels ever written.",
        "known_for": ["Nobel Prize 1982", "Magical Realism", "Colombian Literature"],
    },
    {
        "title": "Sapiens", "emoji": "🧠", "genre": "Non-Fiction",
        "year": "2011", "author": "Yuval Noah Harari", "pages": "443",
        "tagline": "A Brief History of Humankind",
        "bio": "Harari's sweeping history of the human species spans 70,000 years — from the cognitive revolution that made Homo sapiens dominant to the present day. Drawing on biology, anthropology, and economics, it asks why our species conquered the world and where we might be headed.",
        "known_for": ["Cognitive Revolution", "30M+ Copies Sold", "Global Bestseller"],
    },
    {
        "title": "The Catcher in the Rye", "emoji": "🧢", "genre": "Coming-of-Age",
        "year": "1951", "author": "J.D. Salinger", "pages": "277",
        "tagline": "The Voice of a Generation",
        "bio": "Holden Caulfield's disenchanted narration of his expulsion from prep school and subsequent days wandering New York City became one of the most controversial and beloved coming-of-age stories in literature. A raw, honest portrayal of teenage alienation and the loss of innocence.",
        "known_for": ["Holden Caulfield", "Coming-of-Age Classic", "Banned Books"],
    },
]

# ─────────────────────────────────────────────────────────────────
# HTML TEMPLATE
# ─────────────────────────────────────────────────────────────────
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>BookVault — Classic Book Directory</title>
  <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700;900&family=Inter:wght@300;400;600&display=swap" rel="stylesheet"/>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    :root {
      --bg: #0d0a07; --surface: #161210; --card: #1e1814;
      --border: #2e2620; --accent: #e8a045; --text: #f0ebe3;
      --muted: #7a6e65; --radius: 12px; --green: #6bc98c; --red: #e06060;
    }
    html { scroll-behavior: smooth; }
    body { font-family: 'Inter', sans-serif; background: var(--bg); color: var(--text); min-height: 100vh; }

    header {
      background: var(--surface); border-bottom: 1px solid var(--border);
      padding: 0 32px; display: flex; align-items: center;
      justify-content: space-between; height: 64px; position: sticky; top: 0; z-index: 100;
    }
    .logo { font-family: 'Playfair Display', serif; font-size: 1.5rem; font-weight: 900; color: var(--accent); letter-spacing: -0.5px; }
    .logo span { color: var(--text); }
    .header-sub { font-size: 0.75rem; color: var(--muted); letter-spacing: 1.5px; text-transform: uppercase; }
    .health-dot { width: 8px; height: 8px; border-radius: 50%; background: #555; display: inline-block; margin-right: 6px; transition: background 0.3s; }
    .health-dot.ok { background: var(--green); }
    .health-status { font-size: 0.72rem; color: var(--muted); display: flex; align-items: center; }

    main { max-width: 1280px; margin: 0 auto; padding: 40px 24px 80px; }
    .hero { text-align: center; margin-bottom: 48px; }
    .hero h1 { font-family: 'Playfair Display', serif; font-size: clamp(2.5rem, 6vw, 5rem); font-weight: 900; line-height: 1.05; color: var(--text); }
    .hero h1 em { color: var(--accent); font-style: italic; }
    .hero p { margin-top: 14px; color: var(--muted); font-size: 1.05rem; max-width: 520px; margin-left: auto; margin-right: auto; }
    .hero-stats { display: flex; gap: 32px; justify-content: center; margin-top: 28px; flex-wrap: wrap; }
    .stat { text-align: center; }
    .stat-num { font-family: 'Playfair Display', serif; font-size: 2rem; font-weight: 700; color: var(--accent); }
    .stat-label { font-size: 0.7rem; color: var(--muted); letter-spacing: 1.5px; text-transform: uppercase; margin-top: 2px; }

    .controls { display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 32px; align-items: center; }
    .search-wrap { flex: 1; min-width: 240px; position: relative; }
    .search-wrap input { width: 100%; background: var(--surface); border: 1px solid var(--border); color: var(--text); padding: 10px 16px 10px 40px; border-radius: 8px; font-size: 0.9rem; outline: none; }
    .search-wrap input:focus { border-color: var(--accent); }
    .search-icon { position: absolute; left: 14px; top: 50%; transform: translateY(-50%); color: var(--muted); }
    .filter-bar { display: flex; gap: 8px; flex-wrap: wrap; }
    .filter-btn { background: var(--surface); border: 1px solid var(--border); color: var(--muted); padding: 8px 14px; border-radius: 6px; font-size: 0.78rem; cursor: pointer; letter-spacing: 0.5px; transition: all 0.2s; }
    .filter-btn:hover, .filter-btn.active { background: var(--accent); border-color: var(--accent); color: #0d0a07; font-weight: 600; }

    .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 20px; }
    .card {
      background: var(--card); border: 1px solid var(--border); border-radius: var(--radius);
      padding: 24px; cursor: pointer; transition: all 0.2s; position: relative; overflow: hidden;
    }
    .card::before { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px; background: var(--accent); transform: scaleX(0); transition: transform 0.25s; transform-origin: left; }
    .card:hover { border-color: #3e342c; transform: translateY(-3px); box-shadow: 0 12px 32px rgba(0,0,0,0.4); }
    .card:hover::before { transform: scaleX(1); }
    .card-emoji { font-size: 2.4rem; margin-bottom: 14px; display: block; }
    .card-title { font-family: 'Playfair Display', serif; font-size: 1.05rem; font-weight: 700; color: var(--text); margin-bottom: 4px; line-height: 1.3; }
    .card-author { font-size: 0.78rem; color: var(--accent); margin-bottom: 8px; font-weight: 600; letter-spacing: 0.3px; }
    .card-tagline { font-size: 0.8rem; color: var(--muted); line-height: 1.5; }
    .card-tags { display: flex; gap: 6px; margin-top: 14px; flex-wrap: wrap; }
    .tag { font-size: 0.65rem; padding: 3px 8px; border-radius: 4px; letter-spacing: 0.5px; font-weight: 600; text-transform: uppercase; }
    .tag-genre { background: rgba(232,160,69,0.15); color: var(--accent); border: 1px solid rgba(232,160,69,0.25); }
    .tag-year { background: rgba(255,255,255,0.06); color: var(--muted); border: 1px solid var(--border); }

    /* MODAL */
    .modal-overlay {
      display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.75);
      z-index: 1000; align-items: center; justify-content: center; padding: 16px;
    }
    .modal-overlay.open { display: flex; }
    .modal {
      background: var(--card); border: 1px solid #3e342c; border-radius: 16px;
      max-width: 600px; width: 100%; max-height: 90vh; overflow-y: auto; padding: 36px; position: relative;
    }
    .modal-close { position: absolute; top: 16px; right: 16px; background: var(--surface); border: 1px solid var(--border); color: var(--muted); width: 32px; height: 32px; border-radius: 6px; cursor: pointer; font-size: 1rem; display: flex; align-items: center; justify-content: center; }
    .modal-emoji { font-size: 3rem; margin-bottom: 16px; display: block; }
    .modal-title { font-family: 'Playfair Display', serif; font-size: 1.8rem; font-weight: 900; color: var(--text); margin-bottom: 4px; }
    .modal-author { font-size: 0.9rem; color: var(--accent); font-weight: 600; margin-bottom: 6px; }
    .modal-tagline { font-size: 0.85rem; color: var(--muted); margin-bottom: 16px; }
    .modal-tags { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 20px; }
    .modal-bio { font-size: 0.88rem; color: #c0b8b0; line-height: 1.75; margin-bottom: 24px; }
    .modal-facts { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; margin-bottom: 24px; }
    .fact { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 12px; }
    .fact-label { font-size: 0.65rem; color: var(--muted); text-transform: uppercase; letter-spacing: 1px; margin-bottom: 4px; }
    .fact-val { font-size: 0.9rem; color: var(--text); font-weight: 600; }
    .known-for-label { font-size: 0.7rem; color: var(--muted); text-transform: uppercase; letter-spacing: 1px; margin-bottom: 10px; }
    .chips { display: flex; gap: 8px; flex-wrap: wrap; }
    .chip { background: rgba(232,160,69,0.12); border: 1px solid rgba(232,160,69,0.2); color: var(--accent); font-size: 0.75rem; padding: 5px 12px; border-radius: 20px; }

    /* FEEDBACK SECTION */
    .section { margin-top: 72px; }
    .section-header { font-family: 'Playfair Display', serif; font-size: 1.8rem; font-weight: 900; color: var(--text); margin-bottom: 8px; }
    .section-sub { font-size: 0.85rem; color: var(--muted); margin-bottom: 32px; }
    .feedback-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 32px; }
    @media (max-width: 768px) { .feedback-grid { grid-template-columns: 1fr; } }
    .form-card { background: var(--card); border: 1px solid var(--border); border-radius: var(--radius); padding: 28px; }
    .form-title { font-size: 0.75rem; color: var(--muted); letter-spacing: 1.5px; text-transform: uppercase; margin-bottom: 20px; }
    .form-group { margin-bottom: 16px; }
    .form-group label { display: block; font-size: 0.75rem; color: var(--muted); text-transform: uppercase; letter-spacing: 1px; margin-bottom: 6px; }
    .form-group input, .form-group textarea {
      width: 100%; background: var(--surface); border: 1px solid var(--border);
      color: var(--text); padding: 10px 14px; border-radius: 8px; font-size: 0.88rem;
      outline: none; font-family: inherit; transition: border-color 0.2s;
    }
    .form-group input:focus, .form-group textarea:focus { border-color: var(--accent); }
    .form-group textarea { min-height: 90px; resize: vertical; }
    .btn-submit {
      width: 100%; background: var(--accent); color: #0d0a07; border: none;
      padding: 12px; border-radius: 8px; font-weight: 700; font-size: 0.85rem;
      letter-spacing: 1px; text-transform: uppercase; cursor: pointer; transition: opacity 0.2s;
      font-family: inherit;
    }
    .btn-submit:hover { opacity: 0.9; }
    .btn-submit:disabled { opacity: 0.5; cursor: not-allowed; }

    .reviews-card { background: var(--card); border: 1px solid var(--border); border-radius: var(--radius); padding: 28px; }
    .reviews-title { font-size: 0.75rem; color: var(--muted); letter-spacing: 1.5px; text-transform: uppercase; margin-bottom: 20px; }
    .review-card { border-bottom: 1px solid var(--border); padding: 14px 0; }
    .review-card:last-child { border-bottom: none; }
    .review-top { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 6px; }
    .review-name { font-size: 0.88rem; font-weight: 700; color: var(--text); }
    .review-email { font-size: 0.72rem; color: var(--muted); margin-top: 2px; }
    .review-date { font-size: 0.7rem; color: var(--muted); }
    .review-msg { font-size: 0.82rem; color: #b0a89e; line-height: 1.55; }
    .review-empty { font-size: 0.85rem; color: var(--muted); padding: 20px 0; text-align: center; }

    .toast { position: fixed; bottom: 32px; right: 32px; background: var(--surface); border: 1px solid var(--border); color: var(--text); padding: 12px 20px; border-radius: 8px; font-size: 0.85rem; opacity: 0; transform: translateY(10px); transition: all 0.3s; z-index: 2000; pointer-events: none; }
    .toast.show { opacity: 1; transform: translateY(0); }
    .toast.success { border-color: var(--green); color: var(--green); }
    .toast.error { border-color: var(--red); color: var(--red); }

    .no-results { text-align: center; padding: 60px 20px; color: var(--muted); font-size: 0.95rem; }

    footer { text-align: center; padding: 40px 16px; border-top: 1px solid var(--border); font-size: 0.75rem; color: var(--muted); letter-spacing: 0.5px; }
    footer span { color: var(--accent); }
  </style>
</head>
<body>

<header>
  <div>
    <div class="logo">Book<span>Vault</span></div>
    <div class="header-sub">Classic Book Directory</div>
  </div>
  <div class="health-status">
    <span class="health-dot" id="healthDot"></span>
    <span id="healthText">Checking...</span>
  </div>
</header>

<main>
  <div class="hero">
    <h1>Discover <em>Timeless</em> Books</h1>
    <p>A curated collection of the world's greatest literary works, from ancient classics to modern masterpieces.</p>
    <div class="hero-stats">
      <div class="stat"><div class="stat-num" id="statTotal">—</div><div class="stat-label">Books</div></div>
      <div class="stat"><div class="stat-num" id="statGenres">—</div><div class="stat-label">Genres</div></div>
      <div class="stat"><div class="stat-num" id="statAuthors">—</div><div class="stat-label">Authors</div></div>
    </div>
  </div>

  <div class="controls">
    <div class="search-wrap">
      <span class="search-icon">🔍</span>
      <input type="text" id="searchInput" placeholder="Search by title, author, or genre…"/>
    </div>
    <div class="filter-bar" id="filterBar"></div>
  </div>

  <div class="grid" id="bookGrid"></div>

  <!-- REVIEW SECTION -->
  <div class="section">
    <div class="section-header">📖 Reader Reviews</div>
    <div class="section-sub">Share your thoughts on these literary masterpieces</div>
    <div class="feedback-grid">
      <div class="form-card">
        <div class="form-title">Leave a Review</div>
        <div class="form-group"><label>Your Name</label><input type="text" id="fbName" placeholder="e.g. Jane Smith"/></div>
        <div class="form-group"><label>Email</label><input type="email" id="fbEmail" placeholder="jane@email.com"/></div>
        <div class="form-group"><label>Your Review</label><textarea id="fbMessage" placeholder="What are your thoughts on these books?"></textarea></div>
        <button class="btn-submit" id="submitBtn" onclick="submitReview()">SUBMIT REVIEW</button>
      </div>
      <div class="reviews-card">
        <div class="reviews-title">Recent Reviews</div>
        <div id="reviewList"><div class="review-empty">Loading reviews...</div></div>
      </div>
    </div>
  </div>
</main>

<footer>
  Built with ❤️ on <span>AWS ECS Fargate</span> · Stockholm (eu-north-1) · Powered by <span>BookVault</span>
</footer>

<!-- MODAL -->
<div class="modal-overlay" id="modalOverlay">
  <div class="modal">
    <button class="modal-close" id="closeBtn">✕</button>
    <span class="modal-emoji" id="mEmoji"></span>
    <div class="modal-title" id="mTitle"></div>
    <div class="modal-author" id="mAuthor"></div>
    <div class="modal-tagline" id="mTagline"></div>
    <div class="modal-tags" id="mTags"></div>
    <div class="modal-bio" id="mBio"></div>
    <div class="modal-facts" id="mFacts"></div>
    <div class="known-for-label">Notable For</div>
    <div class="chips" id="mChips"></div>
  </div>
</div>

<div class="toast" id="toast"></div>

<script>
const BOOKS = {{ books | tojson }};
let activeFilter = 'All';
let searchVal = '';

function getGenres() {
  const g = new Set(BOOKS.map(b => b.genre));
  return ['All', ...Array.from(g).sort()];
}
function renderFilters() {
  const bar = document.getElementById('filterBar');
  bar.innerHTML = getGenres().map(g =>
    `<button class="filter-btn ${g===activeFilter?'active':''}" onclick="setFilter('${g}')">${g}</button>`
  ).join('');
}
function setFilter(g) { activeFilter=g; renderFilters(); renderGrid(); }
function renderGrid() {
  const grid = document.getElementById('bookGrid');
  const q = searchVal.toLowerCase();
  const filtered = BOOKS.filter(b => {
    const matchFilter = activeFilter==='All' || b.genre===activeFilter;
    const matchSearch = !q || b.title.toLowerCase().includes(q) || b.author.toLowerCase().includes(q) || b.genre.toLowerCase().includes(q);
    return matchFilter && matchSearch;
  });
  if (!filtered.length) { grid.innerHTML='<div class="no-results">📚 No books found. Try a different search.</div>'; return; }
  grid.innerHTML = filtered.map((b,i) => `
    <div class="card" onclick="openModal(${BOOKS.indexOf(b)})">
      <span class="card-emoji">${b.emoji}</span>
      <div class="card-title">${b.title}</div>
      <div class="card-author">${b.author} · ${b.year}</div>
      <div class="card-tagline">${b.tagline}</div>
      <div class="card-tags">
        <span class="tag tag-genre">${b.genre}</span>
        <span class="tag tag-year">${b.pages} pp</span>
      </div>
    </div>
  `).join('');
}

// Stats
document.getElementById('statTotal').textContent = BOOKS.length;
document.getElementById('statGenres').textContent = new Set(BOOKS.map(b=>b.genre)).size;
document.getElementById('statAuthors').textContent = new Set(BOOKS.map(b=>b.author)).size;

// Health check
async function checkHealth() {
  try {
    const r = await fetch('/health');
    const d = await r.json();
    const dot = document.getElementById('healthDot');
    const txt = document.getElementById('healthText');
    if (d.db === 'ok') { dot.classList.add('ok'); txt.textContent = 'RDS Connected'; }
    else { txt.textContent = 'DB: ' + d.db; }
  } catch(e) { document.getElementById('healthText').textContent = 'Offline'; }
}
checkHealth();

function openModal(i) {
  const b = BOOKS[i];
  document.getElementById('mEmoji').textContent = b.emoji;
  document.getElementById('mTitle').textContent = b.title;
  document.getElementById('mAuthor').textContent = 'by ' + b.author;
  document.getElementById('mTagline').textContent = b.tagline;
  document.getElementById('mBio').textContent = b.bio;
  document.getElementById('mTags').innerHTML = `<span class="tag tag-genre">${b.genre}</span><span class="tag tag-year">${b.year}</span>`;
  document.getElementById('mFacts').innerHTML = [
    {label:'Author',val:b.author},{label:'Year',val:b.year},
    {label:'Pages',val:b.pages},{label:'Genre',val:b.genre}
  ].map(f=>`<div class="fact"><div class="fact-label">${f.label}</div><div class="fact-val">${f.val}</div></div>`).join('');
  document.getElementById('mChips').innerHTML = b.known_for.map(k=>`<span class="chip">${k}</span>`).join('');
  document.getElementById('modalOverlay').classList.add('open');
  document.body.style.overflow='hidden';
}
function closeModal() {
  document.getElementById('modalOverlay').classList.remove('open');
  document.body.style.overflow='';
}
document.getElementById('modalOverlay').addEventListener('click',function(e){if(e.target===this)closeModal();});
document.getElementById('closeBtn').addEventListener('click',closeModal);
document.addEventListener('keydown',e=>{if(e.key==='Escape')closeModal();});
document.getElementById('searchInput').addEventListener('input',function(){searchVal=this.value;renderGrid();});

let toastTimer;
function showToast(msg,type='success'){
  const t=document.getElementById('toast');
  t.textContent=msg; t.className=`toast ${type} show`;
  clearTimeout(toastTimer);
  toastTimer=setTimeout(()=>t.className='toast',3500);
}

async function submitReview(){
  const name=document.getElementById('fbName').value.trim();
  const email=document.getElementById('fbEmail').value.trim();
  const message=document.getElementById('fbMessage').value.trim();
  if(!name||!email||!message){showToast('Please fill in all fields.','error');return;}
  const btn=document.getElementById('submitBtn');
  btn.disabled=true; btn.textContent='SUBMITTING...';
  try {
    const fd=new FormData();
    fd.append('name',name); fd.append('email',email); fd.append('message',message);
    const res=await fetch('/review',{method:'POST',body:fd});
    const data=await res.json();
    if(res.ok){
      showToast('✅ Review saved to RDS!','success');
      document.getElementById('fbName').value='';
      document.getElementById('fbEmail').value='';
      document.getElementById('fbMessage').value='';
      loadReviews();
    } else {
      showToast('❌ '+(data.error||'Error occurred.'),'error');
    }
  } catch(e){ showToast('❌ Network error. Try again.','error'); }
  btn.disabled=false; btn.textContent='SUBMIT REVIEW';
}

async function loadReviews(){
  try {
    const res=await fetch('/reviews');
    const data=await res.json();
    const list=document.getElementById('reviewList');
    if(!data.reviews||!data.reviews.length){
      list.innerHTML='<div class="review-empty">No reviews yet. Be the first! 📚</div>';return;
    }
    list.innerHTML=data.reviews.slice(0,6).map(f=>`
      <div class="review-card">
        <div class="review-top">
          <div>
            <div class="review-name">${esc(f.name)}</div>
            <div class="review-email">${esc(f.email)}</div>
          </div>
          <div class="review-date">${fmtDate(f.created_at)}</div>
        </div>
        <div class="review-msg">${esc(f.message)}</div>
      </div>
    `).join('');
  } catch(e){ document.getElementById('reviewList').innerHTML='<div class="review-empty">Could not load reviews.</div>'; }
}

function esc(s){return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}
function fmtDate(d){if(!d)return'';return new Date(d).toLocaleDateString('en-GB',{month:'short',day:'numeric',year:'numeric'});}

renderFilters(); renderGrid(); loadReviews();
</script>
</body>
</html>
"""

# ─────────────────────────────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE, books=BOOKS)


@app.route("/health")
def health():
    """Health check — also verifies RDS connectivity"""
    db_status = "ok"
    try:
        conn = get_db_connection()
        conn.close()
    except Exception as e:
        db_status = f"error: {str(e)}"
    return jsonify({"status": "ok", "db": db_status, "app": "BookVault Directory", "version": "1.0.0"})


@app.route("/api/books")
def api_books():
    return jsonify({"books": BOOKS, "total": len(BOOKS)})


@app.route("/review", methods=["POST"])
def submit_review():
    """Receive user review and INSERT into Amazon RDS (MySQL)"""
    name    = request.form.get("name", "").strip()
    email   = request.form.get("email", "").strip()
    message = request.form.get("message", "").strip()

    if not name or not email or not message:
        return jsonify({"error": "All fields are required."}), 400

    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO reviews (name, email, message) VALUES (%s, %s, %s)",
                (name, email, message)
            )
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "Review saved to RDS successfully."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/reviews")
def view_reviews():
    """Return all reviews from RDS — used by frontend"""
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT id, name, email, message, created_at FROM reviews ORDER BY created_at DESC LIMIT 50"
            )
            data = cursor.fetchall()
        conn.close()
        for row in data:
            if row.get("created_at"):
                row["created_at"] = str(row["created_at"])
        return jsonify({"reviews": data, "total": len(data)})
    except Exception as e:
        return jsonify({"error": str(e), "reviews": []}), 500


# ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    init_db()   # Create table if not exists
    app.run(host="0.0.0.0", port=5000, debug=False)
