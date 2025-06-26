document.addEventListener('DOMContentLoaded', function () {
  const isAuthenticated = window.userInfo.isAuthenticated === 'true';
  const isGM = window.userInfo.isGM === 'true';

  const searchBar = new bootstrap.Collapse('#searchBar', { toggle: false });
  const annoncesDropdown = new bootstrap.Dropdown(document.querySelector('#annoncesDropdown'));
  const informationsDropdown = new bootstrap.Dropdown(document.querySelector('#informationsDropdown'));

  let steps = [
    {
      title: "Bienvenue",
      intro: "Bienvenue sur <strong>QuestMaster</strong>, l'application de gestion des annonces du Club JDR.<br>Tout commence sur cette page d'accueil !"
    },
    {
      element: '#annoncesMenu',
      intro: "Ce menu vous permet d'accéder aux différentes pages relatives aux annonces.",
      title: "Menu annonces"
    },
    {
      element: '#openGames',
      intro: "Accédez aux annonces ouvertes, où vous pouvez chercher une partie.",
      title: "Annonces ouvertes"
    },
    {
      element: '#myPlayerGames',
      intro: "Accédez à la liste des parties sur lesquelles vous jouez.<br>"+
        "<div class='alert alert-primary' role='alert'>Vous devez <strong>être connecté</strong> pour avoir accès à cette option du menu.</div>",
      title: "Mes parties"
    },
    {
      id: 'loginStep',
      element: '#loginButton',
      intro: "Connectez-vous à <strong>QuestMaster</strong> en cliquant sur ce bouton.<br>"+
        "<div class='alert alert-primary' role='alert'>Vous serez redirigé vers Discord pour vous authentifier.<br>"+
        "Vous devez avoir le rôle <strong>Joueur·euses</strong> sur notre serveur pour pouvoir vous inscrire aux parties.</div>",
      title: "Me connecter"
    },
    {
      element: '#myGmGames',
      intro: "Accédez à la liste des parties pour lesquelles vous êtes MJ.<br>" +
        "<div class='alert alert-primary' role='alert'>Vous devez <strong>être connecté et avoir le rôle MJ</strong> pour avoir accès à cette option du menu.</div>",
      title: "Mes annonces"
    },
    {
      element: '#postNewGame',
      intro: "Accédez au formulaire pour proposer une partie.<br>" +
        "<div class='alert alert-primary' role='alert'>Vous devez <strong>être connecté et avoir le rôle MJ</strong> pour avoir accès à cette option du menu.</div>",
      title: "Poster une annonce"
    },
    {
      element: '#infoMenu',
      intro: "Ce menu vous permet d'accéder aux différentes pages d'informations.",
      title: "Informations"
    },
    {
      element: '#calendarLink',
      intro: "Consultez le calendrier des parties, mois par mois.",
      title: "Calendrier"
    },
    {
      element: '#statsLink',
      intro: "Accédez aux statistiques de la plateforme.",
      title: "Statistiques"
    },
    {
      element: '#systemsLink',
      intro: "Consultez la liste des systèmes de jeu.",
      title: "Systèmes"
    },
    {
      element: '#vttsLink',
      intro: "Liste des VTTs utilisés sur notre serveur.",
      title: "VTTs"
    },
    {
      element: '#game-cards-container',
      intro: "Voici la liste des annonces ouvertes.<br><br>Le code couleur est le suivant :<br>" +
        "- <span class='text-success fw-semibold'>Vert</span> : les OS,<br>" +
        "- <span class='text-primary fw-semibold'>Bleu</span> : les campagnes,<br><br>" +
        "D'autres couleurs peuvent apparaître lors des recherches :<br>" +
        "- <span class='text-dark fw-semibold'>Noir</span> : annonces complètes,<br>" +
        "- <span class='text-danger fw-semibold'>Rouge</span> : archivées,<br>" +
        "- <span class='text-secondary fw-semibold'>Gris</span> : brouillons (non publiées).",
      title: "Liste des annonces"
    },
    {
      element: '#searchBar',
      intro: "Voici la barre de recherche avancée.<br>Filtrez par nom, système, VTT, type de partie, statut ou restriction.",
      title: "Recherche avancée"
    },
    {
      element: '#search-submit-button',
      intro: "Cliquez ici pour lancer la recherche selon vos critères.",
      title: "Rechercher"
    },
    {
      element: document.querySelector('.game-card'),
      intro: "Voici un exemple d'annonce. Cliquons dessus pour accéder aux détails.",
      title: "Détails d'annonce."
    }
  ];

  if (isAuthenticated) {
    steps = steps.filter(step => step.id !== 'loginStep');
  }

  const mainIntro = introJs();

  mainIntro.setOptions({
    steps: steps,
    nextLabel: 'Suivant',
    prevLabel: 'Précédent',
    doneLabel: 'Terminé',
    showBullets: true,
    showProgress: false,
    exitOnOverlayClick: false,
    disableInteraction: true
  });

  mainIntro.onbeforechange(function (targetElement) {
    if (!targetElement) {
      return; // No target, probably the 'done' button → skip
    }
    if (targetElement.id === 'searchBar') {
      if (!targetElement.classList.contains('show')) {
        searchBar.show();
        return new Promise(resolve => setTimeout(resolve, 400));
      }
    }
    if (targetElement.id === 'game-cards-container'){
      informationsDropdown.hide();
    }
    if (targetElement.id === 'annoncesMenu') {
      annoncesDropdown.show();
    }
    if (targetElement.id === 'infoMenu') {
      annoncesDropdown.hide();
      informationsDropdown.show();
    }
  });

  mainIntro.oncomplete(() => {
    window.location.href = "/demo/inscription/";
  });

  mainIntro.onexit(() => {
    searchBar.hide();
    annoncesDropdown.hide();
    informationsDropdown.hide();
  });

  mainIntro.start();
});
