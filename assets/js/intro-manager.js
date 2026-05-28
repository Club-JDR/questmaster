// @ts-nocheck
import introJs from 'intro.js';

const { path, isAuthenticated, isGM } = globalThis.pageContext;

// Compact inline notes — much lighter than full DaisyUI alert components inside tooltips
const infoNote = (text) => `<p class="text-xs text-info mt-2"><i class="ph ph-info"></i> ${text}</p>`;
const warnNote = (text) => `<p class="text-xs text-warning mt-2 font-medium"><i class="ph ph-warning"></i> ${text}</p>`;
const errNote = (text) => `<p class="text-xs text-error mt-2 font-semibold"><i class="ph ph-warning-circle"></i> ${text}</p>`;

const INTRO_DEFAULTS = {
  nextLabel: 'Suivant',
  prevLabel: 'Précédent',
  doneLabel: 'Terminé',
  showBullets: true,
  showProgress: false,
  exitOnOverlayClick: false,
  disableInteraction: true,
  exitOnEsc: false,
};

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

function showOutroMessage() {
  const redirectUrl = '/';
  const outro = introJs.tour();
  outro.setOptions({
    ...INTRO_DEFAULTS,
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
        title: "Retour à l'accueil"
      }
    ],
  });
  outro.oncomplete(() => globalThis.location.href = redirectUrl);
  outro.onexit(() => globalThis.location.href = redirectUrl);
  outro.start();
}

function runHomepageIntro() {
  const searchBarDetails = document.getElementById('searchBar');
  const annoncesDetails = document.querySelector('#annoncesMenu')?.closest('details');
  const informationsDetails = document.querySelector('#infoMenu')?.closest('details');

  // Which step ids live inside each dropdown
  const annoncesIds = new Set(['annoncesMenu', 'openGames', 'myPlayerGames', 'myGmGames', 'postNewGame']);
  const infoIds = new Set(['infoMenu', 'trophiesLink', 'trophiesLeaderboardLink', 'calendarLink', 'statsLink', 'systemsLink', 'vttsLink']);

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
      intro: "Accédez à la liste des parties sur lesquelles vous jouez." +
        infoNote("Vous devez <strong>être connecté</strong> pour avoir accès à cette option."),
      title: "Mes parties"
    },
    {
      id: 'loginStep',
      element: '#loginButton',
      intro: "Connectez-vous à <strong>QuestMaster</strong> en cliquant sur ce bouton." +
        infoNote("Vous serez redirigé vers Discord pour vous authentifier. Vous devez avoir le rôle <strong>Joueur·euses</strong> sur notre serveur pour pouvoir vous inscrire aux parties."),
      title: "Me connecter"
    },
    {
      element: '#myGmGames',
      intro: "Accédez à la liste des parties pour lesquelles vous êtes MJ." +
        infoNote("Vous devez <strong>être connecté et avoir le rôle MJ</strong> pour avoir accès à cette option."),
      title: "Mes annonces"
    },
    {
      element: '#postNewGame',
      intro: "Accédez au formulaire pour proposer une partie." +
        infoNote("Vous devez <strong>être connecté et avoir le rôle MJ</strong> pour avoir accès à cette option."),
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
      title: "Badges"
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
      intro: "Voici la liste des annonces ouvertes.<br><br>La couleur de la bordure indique le type :<br>" +
        "- <span class='text-success font-semibold'>Vert</span> : One Shot,<br>" +
        "- <span class='text-primary font-semibold'>Bleu</span> : Campagne.<br><br>" +
        "Un ruban dans le coin supérieur droit indique le statut :<br>" +
        "- <span class='text-info font-semibold'>Bleu</span> : brouillon,<br>" +
        "- <span class='text-base-content font-semibold'>Sombre</span> : complète,<br>" +
        "- <span class='text-error font-semibold'>Rouge</span> : archivée.",
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
      element: '.game-card',
      intro: "Voici un exemple d'annonce. Cliquons dessus pour accéder aux détails.",
      title: "Détails d'annonce."
    }
  ];

  if (isAuthenticated) {
    steps = steps.filter(step => step.id !== 'loginStep');
  }

  const intro = introJs.tour();
  intro.setOptions({ ...INTRO_DEFAULTS, steps });

  intro.onbeforechange(function (target) {
    const id = target?.id;
    const needsAnnonces = !!id && annoncesIds.has(id);
    const needsInfo = !!id && infoIds.has(id);

    if (annoncesDetails) annoncesDetails.open = needsAnnonces;
    if (informationsDetails) informationsDetails.open = needsInfo;

    if (id === 'searchBar' && !target.open) {
      target.open = true;
      return new Promise(resolve => setTimeout(resolve, 300));
    }

    if (needsAnnonces || needsInfo) {
      return new Promise(resolve => setTimeout(() => {
        if (annoncesDetails) annoncesDetails.open = needsAnnonces;
        if (informationsDetails) informationsDetails.open = needsInfo;
        resolve();
      }, 50));
    }
  });

  intro.oncomplete(() => globalThis.location.href = "/demo/inscription/");
  intro.onexit(() => {
    if (searchBarDetails) searchBarDetails.open = false;
    if (annoncesDetails) annoncesDetails.open = false;
    if (informationsDetails) informationsDetails.open = false;
    showOutroMessage();
  });

  intro.start();
}

function runRegistrationIntro() {
  const intro = introJs.tour();
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
      intro: "Cliquez sur ce bouton pour vous inscrire." +
        infoNote("Vous devez être connecté et avoir le rôle <strong>Joueur·euses</strong> sur notre serveur pour pouvoir vous inscrire.") +
        errNote("Merci de <strong>bien lire</strong> l'annonce et de vérifier que <strong>vous êtes disponibles</strong> sur toutes les dates.<br>Une inscription vaut engagement. <strong>Tout manquement pourra être sanctionné.</strong>"),
      title: "S'inscrire"
    },
    {
      element: '#channel-btn',
      intro: "Cliquer sur ce bouton vous permettra d'accéder directement au salon de partie sur Discord." +
        infoNote("Vous devez être inscrit·e sur l'annonce (ou en être le·a MJ) pour voir ce bouton."),
      title: "Canal Discord"
    },
    {
      element: '#alert-btn',
      intro: "Cliquer sur ce bouton vous permettra de signaler aux admins un comportement contraire au règlement.<br>Suite à ce signalement, vous serez recontacté par un admin en MP." +
        infoNote("Vous devez être inscrit·e sur l'annonce (ou en être le·a MJ) pour faire un signalement."),
      title: "Faire un signalement"
    },
    {
      element: '#sessions-list',
      intro: "La liste des sessions de la partie se trouve dans cette zone.<br>Votre MJ pourra ajouter des sessions ou les modifier au fur et à mesure.",
      title: "Sessions de jeu"
    },
    {
      element: '#calendarTriggerBtn',
      intro: "Vous pouvez ajouter la session dans votre calendrier en cliquant sur ce bouton.",
      title: "Ajouter au calendrier"
    }
  ];

  const showYesNo = !(isAuthenticated && isGM);

  if (showYesNo) {
    steps.push({
      intro: `
        <p>Souhaitez-vous découvrir comment poster une annonce en tant que MJ ?</p>
        <div class="flex gap-2 mt-3">
          <button id="btn-yes-final" class="btn btn-success btn-sm">Oui</button>
          <button id="btn-no-final" class="btn btn-error btn-sm">Non</button>
        </div>
      `,
      title: "Poster une annonce"
    });
  }

  intro.setOptions({ ...INTRO_DEFAULTS, steps });

  if (showYesNo) {
    intro.onchange(function () {
      const isYesNoStep = this._currentStep === steps.length - 1;
      const buttons = document.querySelector('.introjs-tooltipbuttons');
      if (buttons) buttons.style.display = isYesNoStep ? 'none' : '';
    });
  }

  document.addEventListener('click', (event) => {
    const yes = document.getElementById('btn-yes-final');
    const no = document.getElementById('btn-no-final');

    if (event.target === yes) {
      hasRedirected = true;
      intro.exit();
      globalThis.location.href = "/demo/poster/";
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
      globalThis.location.href = "/demo/poster/";
    }
  });

  intro.onexit(() => {
    if (!hasRedirected) {
      showOutroMessage();
    }
  });

  intro.start();
}


function runPostGameIntro() {
  const annoncesDetails = document.querySelector('#annoncesMenu')?.closest('details');
  const intro = introJs.tour();

  // Steps follow the visual form layout: Card 1 → Card 2 → Card 3 → description → bottom row → right sidebar
  intro.setOptions({
    ...INTRO_DEFAULTS,
    steps: [
      // ── Menu entry point ──
      {
        element: '#postNewGame',
        intro: "Cliquez sur ce bouton du menu depuis n'importe quelle page pour accéder à ce formulaire et poster une nouvelle annonce.",
        title: "Poster une annonce"
      },
      // ── Card 1: Nom · Type · Système · VTT ──
      {
        element: '#game_name',
        intro: "Donnez un nom à votre annonce.",
        title: "Nom"
      },
      {
        element: '#sessionType',
        intro: "Cliquez sur <span class='text-success font-semibold'>One Shot</span> ou sur <span class='text-primary font-semibold'>Campagne</span> pour choisir le type de partie.",
        title: "Type de session"
      },
      {
        element: '#game_system',
        intro: "Choisissez le système de jeu utilisé parmi la liste déroulante." +
          infoNote("Si vous ne trouvez pas votre système de jeu, demandez à un Admin de le créer pour vous."),
        title: "Système"
      },
      {
        element: '#game_vtt',
        intro: "Choisissez le VTT utilisé parmi la liste déroulante." +
          infoNote("Si vous ne trouvez pas le VTT que vous souhaitez, demandez à un Admin de le créer pour vous."),
        title: "VTT"
      },
      // ── Card 2: Date · Durée · Fréquence ──
      {
        element: '#game_date',
        intro: "Sélectionnez la date de la première session.",
        title: "Date"
      },
      {
        element: '#lengthGroup',
        intro: "Indiquez le nombre de sessions et la durée moyenne des sessions en heures.",
        title: "Durée"
      },
      {
        element: '#game_frequency',
        intro: "Indiquez la fréquence des sessions (peut rester vide) parmi les choix possibles.",
        title: "Fréquence des sessions"
      },
      // ── Card 3: Joueurs · Sélection · XP · Personnages ──
      {
        element: '#party_size_input',
        intro: "Nombre de places de joueur·euses disponibles.",
        title: "Taille du groupe"
      },
      {
        element: '#party_selection',
        intro: "Activez cette option si vous voulez choisir vos joueur·euses parmi les inscrit·es." +
          infoNote("Si l'option est activée, l'annonce ne se fermera pas automatiquement une fois le nombre maximal de joueur·euses atteint."),
        title: "Sélection de joueur·euses"
      },
      {
        element: '#game_xp',
        intro: "Choisissez le profil de joueur·euses que vous recherchez.",
        title: "Niveau des joueur·euses"
      },
      {
        element: '#game_characters',
        intro: "Indiquez comment se fera la création des personnages.",
        title: "Création de personnages"
      },
      // ── Description ──
      {
        element: '#game_description',
        intro: "Ajoutez le pitch du scénario correspondant à votre annonce.",
        title: "Description"
      },
      {
        element: '#game_complement',
        intro: "Dans ce champ, vous pouvez ajouter des informations supplémentaires. Par exemple : un lien vers un formulaire de sélection, une demande spécifique du MJ, ou tout ce qui ne rentrerait pas dans les cases du formulaire.",
        title: "Informations complémentaires"
      },
      // ── Bottom row: Avertissement · Classification · Ambiance ──
      {
        element: '#restrictionGroup',
        intro: "Cliquez sur <span class='text-success font-semibold'>Tout public</span>, sur <span class='text-warning font-semibold'>16+</span> ou sur <span class='text-error font-semibold'>18+</span> pour définir la limite d'âge de votre annonce.",
        title: "Restriction"
      },
      {
        element: '#restriction_tags',
        intro: "Ajoutez les thèmes sensibles, séparés par des virgules.",
        title: "Thèmes sensibles"
      },
      {
        element: '#classification',
        intro: "Votre partie est plutôt orientée action, investigation, interaction ou horreur ? Utilisez les curseurs pour donner à vos joueur·euses le ton de votre partie.",
        title: "Classification du scénario"
      },
      {
        element: '#ambience',
        intro: "Utilisez les switchs pour définir l'ambiance attendue sur votre partie.",
        title: "Ambiance de la partie"
      },
      // ── Right sidebar: Image · Actions ──
      {
        element: '#imgUrlInput',
        intro: "Collez ici l'URL d'une illustration pour votre annonce." +
          infoNote("Utilisez un lien direct vers l'image (ex: imgur)."),
        title: "Image"
      },
      {
        element: '#gameActionButtons',
        intro: "Il existe plusieurs actions possibles pour enregistrer votre annonce.",
        title: "Enregistrer"
      },
      {
        element: '#saveButton',
        intro: "Crée votre annonce dans QuestMaster sous forme de brouillon :<br>" +
          "- le salon et le rôle de parties <strong>ne sont pas</strong> créés<br>" +
          "- les joueur·euses <strong>ne peuvent pas</strong> s'inscrire<br>" +
          "- l'annonce <strong>n'est pas</strong> publiée sur Discord",
        title: "Enregistrer comme Brouillon"
      },
      {
        element: '#openButton',
        intro: "Idéal pour une partie sans annonce :<br>" +
          "- le salon et le rôle de parties sont créés<br>" +
          "- les joueur·euses peuvent s'inscrire<br>" +
          "- l'annonce <strong>n'est pas publiée</strong> sur Discord",
        title: "Ouvrir sans publier"
      },
      {
        element: '#publishButton',
        intro: "Le grand classique pour poster une annonce :<br>" +
          "- le salon et le rôle de parties sont créés<br>" +
          "- les joueur·euses peuvent s'inscrire<br>" +
          "- l'annonce est publiée sur Discord",
        title: "Publier sur Discord"
      },
      {
        title: "Gérer ses parties",
        intro: "Voyons maintenant comment gérer une annonce."
      }
    ],
  });

  intro.onbeforechange(function (target) {
    if (!annoncesDetails) return;
    const needsOpen = target?.id === 'postNewGame';
    annoncesDetails.open = needsOpen;
    if (needsOpen) {
      return new Promise(resolve => setTimeout(() => {
        annoncesDetails.open = true;
        resolve();
      }, 50));
    }
  });

  intro.onexit(() => showOutroMessage());
  intro.oncomplete(() => globalThis.location.href = '/demo/gerer/');

  intro.start();
}

function runManageIntro() {
  const intro = introJs.tour();
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
      intro: "Ce bouton vous ramène au formulaire vous permettant d'éditer le contenu de votre annonce." +
        warnNote("Une fois l'annonce ouverte, il n'est plus possible de changer le type ou le nom de l'annonce."),
      title: "Éditer"
    },
    {
      element: '#manageButton',
      intro: "Ce bouton vous permet d'inscrire ou de désinscrire des joueur·euses.<br>" +
        "Pour cela, il ouvre une boite de dialogue supplémentaire." +
        warnNote("Veillez à bien lire les consignes de cette boite de dialogue avant toute action."),
      title: "Gérer"
    },
    {
      element: '#addSessionButton',
      intro: "Ce bouton permet d'ajouter une nouvelle session de jeu." +
        infoNote("La session sera inscrite sur le calendrier et comptabilisée dans les statistiques. Un message avec la date et les horaires sera envoyé dans le canal de partie."),
      title: "Ajouter une session"
    },
    {
      element: '#publishButton',
      intro: "Ce bouton permet de poster l'annonce sur Discord lorsqu'elle a été ouverte sans annonce." +
        infoNote("L'annonce ne doit pas avoir déjà été publiée, être en brouillon, ou être déjà complète."),
      title: "Publier"
    },
    {
      element: '#statusButton',
      intro: "Ce bouton permet de changer le statut de votre annonce.<br>" +
        infoNote("Ouverte → les inscriptions sont possibles (bouton jaune « Fermer »).<br>Fermée → les inscriptions ne sont possibles que via « Gérer » (bouton vert « Ouvrir »)."),
      title: "Changer le statut"
    },
    {
      element: '#cloneButton',
      intro: "Ce bouton ouvre un formulaire pour poster une nouvelle annonce. Le formulaire est prérempli avec les informations de cette annonce.",
      title: "Cloner"
    },
    {
      element: '#archiveButton',
      intro: "Ce bouton permet d'archiver votre annonce.<br>Il ouvre une boite de dialogue avec des mentions importantes !" +
        errNote("<strong>Archiver une annonce supprime le salon et le rôle associé et permet la distribution des badges.</strong>"),
      title: "Archiver"
    },
    {
      element: '#sessions-list',
      intro: "Dans chaque session, les boutons <i class='ph ph-pencil-simple'></i> et <i class='ph ph-trash'></i> vous permettent de l'éditer ou de la supprimer.<br>" +
        "Le calendrier et les statistiques mensuelles seront automatiquement mis à jour.",
      title: "Action sur les sessions"
    },
    {
      element: '#event-list',
      intro: "La liste des événements de la partie se trouve dans cette zone.<br>" +
        "Vous pourrez consulter toutes les opérations en lien avec votre annonce (inscriptions, modifications...).",
      title: "Événements"
    },
  ];

  intro.setOptions({ ...INTRO_DEFAULTS, steps });

  intro.oncomplete(() => showOutroMessage());
  intro.onexit(() => showOutroMessage());

  intro.start();
}
