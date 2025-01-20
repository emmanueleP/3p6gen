import os
import json
import requests
from datetime import datetime
from jinja2 import Template

# Configurazione
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')  # Token GitHub per l'API
REPOS = {
    'hemodos': 'emmanueleP/hemodos',
    'abe': 'emmanueleP/abe',
    'glik': 'emmanueleP/glik'
}

# Template HTML per il changelog
CHANGELOG_TEMPLATE = """
<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Changelog {{ app_name }} - 3.6 Gen</title>
    <link rel="stylesheet" href="../../styles.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        .changelog-entry {
            background-color: var(--bg-secondary);
            padding: 2rem;
            border-radius: 8px;
            margin-bottom: 2rem;
        }
        
        .version-header {
            color: var(--accent);
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1.5rem;
        }
        
        .version-date {
            color: var(--text-secondary);
            font-size: 0.9rem;
        }
        
        .change-category {
            margin: 1.5rem 0;
        }
        
        .change-category h3 {
            color: var(--text-secondary);
            margin-bottom: 0.5rem;
        }
        
        .change-list {
            list-style: none;
            padding-left: 1.5rem;
        }
        
        .change-list li {
            position: relative;
            margin-bottom: 0.5rem;
        }
        
        .change-list li::before {
            content: "•";
            color: var(--accent);
            position: absolute;
            left: -1.5rem;
        }
    </style>
</head>
<body>
    <nav>
        <div class="nav-container">
            <a href="../../" class="logo">3.6 Gen</a>
            <div class="nav-links">
                <a href="../../#hemodos">Hemodos</a>
                <a href="../../#abe">Abe Suite</a>
                <a href="../../#glik">Glik</a>
                <a href="../../#contatti">Contatti</a>
                <a href="../../pagnucom/licenze.html">Licenze Pagnucom</a>
            </div>
        </div>
    </nav>

    <main style="padding-top: 6rem;">
        <div class="app-container">
            <h1 style="color: var(--accent); margin-bottom: 2rem;">Changelog {{ app_name }}</h1>

            {% for release in releases %}
            <div class="changelog-entry">
                <div class="version-header">
                    <h2>Versione {{ release.tag_name }}</h2>
                    <span class="version-date">{{ release.published_at }}</span>
                </div>

                <div class="change-category">
                    {% for category, changes in release.changes.items() %}
                    <h3>{{ category }}</h3>
                    <ul class="change-list">
                        {% for change in changes %}
                        <li>{{ change }}</li>
                        {% endfor %}
                    </ul>
                    {% endfor %}
                </div>
            </div>
            {% endfor %}
        </div>
    </main>

    <footer>
        <div class="footer-content">
            <div class="contact-info">
                <h3>Contatti</h3>
                <a href="https://github.com/emmanueleP" class="social-link">
                    <i class="fab fa-github"></i> GitHub
                </a>
            </div>
            <div class="copyright">
                <p>&copy; 2025 Emmanuele Pani. Tutti i diritti riservati.</p>
            </div>
        </div>
    </footer>
</body>
</html>
"""

def parse_release_notes(body):
    """Analizza il testo delle release notes e categorizza i cambiamenti"""
    categories = {
        'Aggiunto': [],
        'Modificato': [],
        'Risolto': [],
        'In Sviluppo': []
    }
    
    current_category = None
    
    if not body:
        return {'Prima Release': ['Prima versione rilasciata']}
    
    for line in body.split('\n'):
        line = line.strip()
        if line.startswith('### '):
            current_category = line[4:].strip()
            if current_category not in categories:
                categories[current_category] = []
        elif line.startswith('- ') and current_category:
            categories[current_category].append(line[2:])
    
    # Rimuovi categorie vuote
    return {k: v for k, v in categories.items() if v}

def get_releases(repo):
    """Ottiene le release da GitHub"""
    headers = {'Authorization': f'token {GITHUB_TOKEN}'} if GITHUB_TOKEN else {}
    url = f'https://api.github.com/repos/{repo}/releases'
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print(f"Errore nel recupero delle release per {repo}: {response.status_code}")
        return []
    
    releases = []
    for release in response.json():
        # Converti la data in formato italiano
        date = datetime.strptime(release['published_at'], '%Y-%m-%dT%H:%M:%SZ')
        formatted_date = date.strftime('%d %B %Y')
        
        releases.append({
            'tag_name': release['tag_name'].replace('v', ''),
            'published_at': formatted_date,
            'changes': parse_release_notes(release['body'])
        })
    
    return releases

def update_changelog(app_name, repo):
    """Aggiorna il file changelog per un'app specifica"""
    releases = get_releases(repo)
    if not releases:
        return
    
    template = Template(CHANGELOG_TEMPLATE)
    html = template.render(app_name=app_name, releases=releases)
    
    # Crea la directory se non esiste
    os.makedirs(f'{app_name.lower()}/changelog', exist_ok=True)
    
    # Salva il file
    with open(f'{app_name.lower()}/changelog/index.html', 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"Changelog aggiornato per {app_name}")

def main():
    """Aggiorna il changelog solo per il repository che ha ricevuto una nuova release"""
    # Ottieni il nome del repository dall'ambiente
    repo_name = os.getenv('REPO_NAME')
    
    if not repo_name:
        print("REPO_NAME non trovato nell'ambiente. Aggiorno tutti i changelog...")
        # Fallback: aggiorna tutti i changelog se eseguito manualmente
        for app_name, repo in REPOS.items():
            update_changelog(app_name.capitalize(), repo)
        return
    
    # Trova l'app corrispondente al repository
    for app_name, repo in REPOS.items():
        if repo.lower() == repo_name.lower():
            print(f"Aggiorno il changelog per {app_name}...")
            update_changelog(app_name.capitalize(), repo)
            break
    else:
        print(f"Nessuna app trovata per il repository {repo_name}")

if __name__ == '__main__':
    main() 