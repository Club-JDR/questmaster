const { path, isAuthenticated, isGM } = window.pageContext;
document.addEventListener('DOMContentLoaded', function () {

  if (path === '/demo/') {
    runHomepageIntro();
  } else if (path === '/demo/inscription/') {
    runRegistrationIntro();
  } else if (path === '/demo/poster/') {
    runPostGameIntro();
  } else if (path === '/demo/gerer/') {
    runManageIntro();
  }
});

function showOutroMessage(message='<br>Je vous redirige vers la page d\'accueil') {
  const redirectUrl='/';
  const outro = introJs();
  outro.setOptions({
    steps: [
      {
        intro: '🎉 Félicitations, Vous savez maintenant utiliser <strong>QuestMaster</strong>.',
        title: "Fin du tour"
      },
      {
        element: '#demoMenu',
        intro: 'Vous pouvez revoir ce tutoriel à tout moment en cliquant sur ce menu.',
        title: "Revoir l'aide"
      },
      {
        intro: 'Je vous redirige maintenant vers la liste des annonces ouvertes.',
        title: 'Retour à l\'accueil'
      }
    ],
    nextLabel: 'Suivant',
    prevLabel: 'Précédent',
    doneLabel: 'Terminé',
    showBullets: true,
    showProgress: false,
    exitOnOverlayClick: false,
    disableInteraction: true,
  });
  outro.oncomplete(() => window.location.href = redirectUrl);
  outro.onexit(() => window.location.href = redirectUrl);

  outro.start();
}

function runHomepageIntro() {
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
      element: '#trophiesLink',
      intro: "Affichez vos badges ou ceux de n'importe quel autre membre du serveur.",
      title: "Classement des badges"
    },
    {
      element: '#trophiesLeaderboardLink',
      intro: "Affichez le classement des badges.",
      title: "Classement des badges"
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

  const intro = introJs();
  intro.setOptions({
    steps,
    nextLabel: 'Suivant',
    prevLabel: 'Précédent',
    doneLabel: 'Terminé',
    showBullets: true,
    showProgress: false,
    exitOnOverlayClick: false,
    disableInteraction: true,
  });

  intro.onbeforechange(function (target) {
    if (!target) return;
    if (target.id === 'searchBar') {
      if (!target.classList.contains('show')) {
        searchBar.show();
        return new Promise(resolve => setTimeout(resolve, 400));
      }
    }
    if (target.id === 'annoncesMenu') annoncesDropdown.show();
    if (target.id === 'infoMenu') {
      annoncesDropdown.hide();
      informationsDropdown.show();
    }
  });

  intro.oncomplete(() => window.location.href = "/demo/inscription/");
  intro.onexit(() => {
    searchBar.hide();
    annoncesDropdown.hide();
    informationsDropdown.hide();
  });

  intro.start();
}

function runRegistrationIntro() {
  const intro = introJs();
  let hasRedirected = false;

  const steps = [
    {
      element: '#game-details-container',
      intro: "Dans ce bloc vous retrouvez les infos relatives à l'annonce.",
      title: "Informations"
    },
    {
      element: '#playerListCard',
      intro: "Ici vous retrouvez la liste des joueur·euses inscrit·es et le nombre de places libres.",
      title: "Liste des inscrit·es"
    },
    {
      element: '#signup-btn',
      intro: "Cliquez sur ce bouton pour vous inscrire.<br>" +
        "<div class='alert alert-primary' role='alert'>Vous devez être connecté et avoir le rôle <strong>Joueur·euses</strong> sur notre serveur pour pouvoir vous inscrire.</div>" +
        "<div class='alert alert-danger' role='alert'>Merci de <strong>bien lire</strong> l'annonce et de vérifier que <strong>vous êtes disponibles</strong> sur toutes les dates de la partie.<br>" +
        "Une inscription à une partie vaut pour un engagement. <strong>Tout engagement qui n'est pas honoré pourra être sanctionné.</strong></div>",
      title: "S'inscrire"
    },
    {
      element: '#alert-btn',
      intro: "<div class='alert alert-primary' role='alert'>Vous devez être inscrit·e sur l'annonce (ou en être le·a MJ) pour faire un signalement.</div>" +
        "Cliquer sur ce bouton vous permettra de signaler aux admins un comportement contraire au règlement de la part du MJ ou d'un·e joueur·euse.<br>" +
        "Suite à ce signalement, vous serez recontacté par un admin en MP.",
      title: "Faire un signalement"
    },
    {
      element: '#sessions-list',
      intro: "La liste des sessions de la partie se trouve dans cette zone.<br>" +
        "Votre MJ pourra ajouter des sessions ou les modifier au fur et à mesure.",
      title: "Sessions de jeu"
    },
    {
      element: document.querySelector('add-to-calendar-button'),
      intro: "Vous pouvez ajouter la session dans votre calendrier en cliquant sur ce bouton.",
      title: "Ajouter au calendrier"
    }
  ];

  const showYesNo = !(isAuthenticated && isGM);

  if (showYesNo) {
    steps.push({
      intro: `
        <p>Souhaitez-vous découvrir comment poster une annonce en tant que MJ ?</p>
        <div class="d-flex gap-2">
          <button id="btn-yes-final" class="btn btn-success">Oui</button>
          <button id="btn-no-final" class="btn btn-danger">Non</button>
        </div>
      `,
      title: "Poster une annonce"
    });
  }

  intro.setOptions({
    steps,
    nextLabel: 'Suivant',
    prevLabel: 'Précédent',
    doneLabel: 'Terminé',
    showBullets: true,
    showProgress: false,
    exitOnOverlayClick: false,
    disableInteraction: true,
    showButtons: !showYesNo
  });

  document.addEventListener('click', (event) => {
    const yes = document.getElementById('btn-yes-final');
    const no = document.getElementById('btn-no-final');

    if (event.target === yes) {
      hasRedirected = true;
      intro.exit();
      window.location.href = "/demo/poster/";
    }
    if (event.target === no) {
      hasRedirected = true;
      intro.exit();
      showOutroMessage();
    }
  });

  intro.oncomplete(() => {
    if (isAuthenticated && isGM) {
      hasRedirected = true;
      window.location.href = "/demo/poster/";
    }
  });

  intro.onexit(() => {
    if (!hasRedirected) {
      showOutroMessage();
    }
  });

  intro.start();
}


function runPostGameIntro(redirectUrl = null) {
  const annoncesDropdown = new bootstrap.Dropdown(document.querySelector('#annoncesDropdown'));
  const gameActionDropdown = new bootstrap.Dropdown(document.querySelector('#gameActionDropdown'));
  const intro = introJs();

  intro.setOptions({
    steps: [
      {
        element: '#postNewGame',
        intro: "Cliquez sur ce bouton du menu depuis n'importe quelle page pour accéder à ce formulaire et poster une nouvelle annonce.",
        title: "Poster une annonce"
      },
      {
        element: '#name',
        intro: "Donnez un nom à votre annonce.",
        title: "Nom"
      },
      {
        element: '#system',
        intro: "Choisissez le système de jeu utilisé parmi la liste déroulante.<br>" +
          "<div class='alert alert-primary' role='alert'>Si vous ne trouvez pas votre système de jeu, demandez à un Admin de le créer pour vous.</div>",
        title: "Système"
      },
      {
        element: '#vtt',
        intro: "Choisissez le VTT utilisé parmi la liste déroulante.<br>" +
          "<div class='alert alert-primary' role='alert'>Si vous ne trouvez pas le VTT que vous souhaitez, demandez à un Admin de le créer pour vous.</div>",
        title: "VTT"
      },
      {
        element: '#description',
        intro: "Ajoutez le pitch du scénario correspondant à votre annonce.",
        title: "Description"
      },
      {
        element: '#complement',
        intro: "Dans ce champ, vous pouvez ajouter des informations supplémentaires. Par exemple : un lien vers un formulaire de sélection, une demande spécifique du MJ, ou tout ce qui ne rentrerais pas dans les cases du formulaire.",
        title: "Informations complémentaires"
      },
      {
        element: '#sessionType',
        intro: "Cliquez sur <span class='text-success fw-semibold'>One Shot</span> ou sur <span class='text-primary fw-semibold'>Campagne</span> pour choisir le type de partie pour votre annonce.",
        title: "Type de session"
      },
      {
        element: '#calendarInput',
        intro: "Sélectionnez la date de la première session.",
        title: "Date"
      },
      {
        element: '#lengthGroup',
        intro: "Indiquez le nombre de sessions et la durée moyenne des sessions en heures.",
        title: "Durée"
      },
      {
        element: '#frequency',
        intro: "Indiquez la fréquence des sessions (peut rester vide) parmi les choix possibles.",
        title: "Fréquence des sessions"
      },
      {
        element: '#party_size',
        intro: "Nombre de places de joueur·euses disponibles.",
        title: "Taille du groupe"
      },
      {
        element: '#party_selection',
        intro: "Activez cette option si vous voulez choisir vos joueur·euses parmi les inscrit·es."+
          "<div class='alert alert-primary' role='alert'>Si l'option est activée, l'annonce ne se fermera pas automatiquement une fois le nombre maximal de joueur·euses atteint.</div>",
        title: "Sélection de joueur·euses"
      },
      {
        element: '#xp',
        intro: "Choisissez le profil de joueur·euses que vous recherchez.",
        title: "Niveau des joueur·euses"
      },
      {
        element: '#characters',
        intro: "Indiquez comment se fera la création des personnages.",
        title: "Création de personnages"
      },
      {
        element: '#restrictionGroup',
        intro: "Cliquez sur <span class='text-success fw-semibold'>Tout public</span>, sur <span class='text-warning fw-semibold'>16+</span> ou sur <span class='text-danger fw-semibold'>18+</span> pour définir la limite d'age votre annonce.",
        title: "Restriction"
      },
      {
        element: 'tags',
        intro: "Ajoutez les thèmes sensibles, séparés par des virgules.",
        title: "Thèmes sensibles"
      },
      {
        element: '#uploadButton',
        intro: "Cliquez sur ce bouton pour ajouter une illustration pour votre annonce."+
          "<div class='alert alert-primary' role='alert'>Le bouton ouvrira une fenêtre afin d'ajouter <strong>l'URL de votre image</strong>.</div>",
        title: "Ajouter une image"
      },
      {
        element: '#classification',
        intro: "Votre partie est plutôt orientée action, investigation qu'intéraction et horreur ? Utilisez les curseurs pour donner à vos joueur·euses le ton de votre partie.",
        title: "Classification du scénario"
      },
      {
        element: '#ambience',
        intro: "Utilisez les switchs pour définir l'ambiance attendue sur votre partie.",
        title: "Ambiance de la partie"
      },
      {
        element: '#gameActionDropdown',
        intro: "Il existe plusieurs actions possibles pour enregistrer votre annonce.",
        title: "Enregistrer"
      },
      {
        element: '#saveButton',
        intro: "Crée votre annonce dans QuestMaster sous forme de brouillon :<br>" +
          "- le salon et le rôle de parties <strong>ne sont pas</strong> créés<br/>" +
          "- les joueur·euses <strong>ne peuvent pas</strong> s'inscrire<br/>" +
          "- l'annonce <strong>n'est pas</strong> publiée sur Discord",
        title: "Enregistrer comme Brouillon"
      },
      {
        element: '#openButton',
        intro: "Idéal pour une partie sans annonce :<br>" +
          "- le salon et le rôle de parties sont créés<br/>" +
          "- les joueur·euses peuvent s'inscrire<br/>" +
          "- l'annonce <strong>n'est pas publiée</strong> sur Discord",
        title: "Ouvrir sans publier"
      },
      {
        element: '#publishButton',
        intro: "Le grand classique pour poster une annonce :<br>" +
          "- le salon et le rôle de parties sont créés<br/>" +
          "- les joueur·euses peuvent s'inscrire<br/>" +
          "- l'annonce est publiée sur Discord",
        title: "Publier sur Discord"
      },
      {
        title: "Gérer ses parties",
        intro: "Voyons maintenant comment gérer une annonce."
      }
    ],
    nextLabel: 'Suivant',
    prevLabel: 'Précédent',
    doneLabel: 'Terminé',
    showBullets: true,
    showProgress: false,
    exitOnOverlayClick: false,
    disableInteraction: true,
  });

  intro.onbeforechange(function (target) {
    if (!target) return;
    if (target.id === 'postNewGame') {
      annoncesDropdown.show();
    }
    if (target.id === 'gameActionDropdown') {
      gameActionDropdown.show();
    }
  });

  intro.onafterchange(function (target) {
    if (!target) return;
    if (target.id !== 'postNewGame') {
      annoncesDropdown.hide();
    }
    if (!['gameActionDropdown', 'saveButton', 'openButton', 'publishButton'].includes(target.id)) {
      gameActionDropdown.hide();
    }
  });

  function redirectToManage() {
    window.location.href = '/demo/gerer/';
  }

  intro.onexit(redirectToManage);
  intro.oncomplete(redirectToManage);

  intro.start();
}

function runManageIntro() {
  const intro = introJs();
  const steps = [
    {
      title: "Comment gérer sa partie en tant que MJ",
      intro: "La page est la même que lorsqu'on veut s'inscrire."
    },
    {
      element: '#actionsPanel',
      intro: "Toutes les actions disponibles se trouvent ici. Passons les en revue.",
      title: "Actions"
    },
    {
      element: '#editButton',
      intro: "Ce bouton vous ramène au formulaire vous permettant d'éditer le contenu de votre annonce.<br>" +
        "<div class='alert alert-primary' role='alert'>Attention, une fois l'annonce ouverte, il n'est plus possible de changer le type ou le nom de l'annonce.</div>",
      title: "Éditer"
    },
    {
      element: '#manageButton',
      intro: "Ce bouton vous permet d'inscrire ou de désinscrire des joueur·euses.<br>" +
        "Pour cela, il ouvre une boite de dialogue supplémentaire.<br>" +
        "<div class='alert alert-primary' role='alert'>Veillez à bien lire les consignes de cette boite de dialogue avant toute action.</div>",
      title: "Gérer"
    },
    {
      element: '#addSessionButton',
      intro: "Ce bouton permet d'ajouter une nouvelle session de jeu.<br>" +
        "<div class='alert alert-primary' role='alert'>La session sera alors automatiquement inscrite sur le calendrier et comptabilisée dans les statistiques mensuelles.<br>" +
        "Un message avec la date et les horaires sera envoyé dans le canal de partie pour prévenir les joueur·euses.</div>",
      title: "Ajouter une session"
    },
    {
      element: '#statusButton',
      intro: "Ce bouton permet de changer le statut de votre annonce.<br>" +
        "<div class='alert alert-primary' role='alert'>Lorsque l'annonce est ouverte, les inscriptions sont possibles et le bouton est jaune avec la mention \"Fermer\".<br>" +
        "Lorsque l'annonce est fermée, les inscriptions ne sont plus possibles que par le MJ via le bouton \"Gérer\" et le bouton est vert avec la mention \"Ouvrir\".</div>",
      title: "Changer le statut"
    },
    {
      element: '#archiveButton',
      intro: "Ce bouton permet d'archiver votre annonce.<br>" +
        "Pour cela, il ouvre une boite de dialogue supplémentaire avec des mentions importantes !<br>" +
        "<div class='alert alert-danger' role='alert'><strong>Archiver une annonce supprime le salon et le rôle associé et permet la distribution des badges.</strong></div>",
      title: "Archiver"
    },
    {
      element: '#cloneButton',
      intro: "Ce bouton ouvre un formulaire pour poster une nouvelle annonce. Le formulaire est prérempli avec les informations de cette annonce.",
      title: "Cloner"
    },
    {
      element: '.calendar-btn-group',
      intro: "Ces boutons vous permettent respectivement d'éditer ou de supprimer la session correspondant.<br>" +
        "Le calendrier et les statistiques mensuelles seront automatiquement mis à jour.<br>" +
        "Un message de modification avec la nouvelle date et les nouveaux horaires sera envoyé dans le canal de partie pour prévenir les joueur·euses.",
      title: "Action sur les sessions"
    },
    {
      element: '#event-list',
      intro: "La liste des événements de la partie se trouve dans cette zone.<br>" +
        "Vous pourrez consulter toutes les opérations en lien avec votre annonce (inscriptions, modifications...).",
      title: "Sessions de jeu"
    },
  ];

  intro.setOptions({
    steps,
    nextLabel: 'Suivant',
    prevLabel: 'Précédent',
    doneLabel: 'Terminé',
    showBullets: true,
    showProgress: false,
    exitOnOverlayClick: false,
    disableInteraction: true,
  });

  intro.oncomplete(() => {
    showOutroMessage();
  });

  intro.onexit(() => {
    showOutroMessage();
  });

  intro.start();
}