document.addEventListener('DOMContentLoaded', function () {
  const isAuthenticated = window.userInfo.isAuthenticated === 'true';
  const isGM = window.userInfo.isGM === 'true';
  const intro = introJs();
  let hasRedirected = false;

  intro.setOptions({
    steps: [
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
        element: '#sessions-list',
        intro: "La liste des sessions de la partie se trouve dans cette zone.<br>" +
          "Votre MJ pourra ajouter des sessions ou les modifier au fur et à mesure.",
        title: "Sessions de jeu"
      },
      {
        element: document.querySelector('add-to-calendar-button'),
        intro: "Vous pouvez ajouter la session dans votre calendrier en cliquant sur ce bouton.",
        title: "Ajouter au calendrier"
      },
      {
        intro: `
          <p>Souhaitez-vous découvrir comment poster une annonce en tant que MJ ?</p>
          <div class="d-flex gap-2">
            <button id="btn-yes-final" class="btn btn-success">Oui</button>
            <button id="btn-no-final" class="btn btn-danger">Non</button>
          </div>
        `,
        title: "Poster une annonce"
      }
    ],
    nextLabel: 'Suivant',
    prevLabel: 'Précédent',
    doneLabel: 'Terminé',
    showBullets: true,
    showProgress: false,
    exitOnOverlayClick: false,
    disableInteraction: true,
    showButtons: false
  });

  document.addEventListener('click', function (event) {
    const yesBtn = document.getElementById('btn-yes-final');
    const noBtn = document.getElementById('btn-no-final');

    if (event.target === yesBtn) {
      hasRedirected = true;
      intro.exit();
      window.location.href = "/demo/poster/";
    }

    if (event.target === noBtn) {
      hasRedirected = true;
      intro.exit();
      showGoodbyeMessage("/");
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
      showGoodbyeMessage("/");
    }
  });

  intro.start();
});

function showGoodbyeMessage(redirectUrl) {
  const outro = introJs();

  outro.setOptions({
    steps: [
      {
        intro: `
          <p>🎉 C’est la fin du tour ! Merci pour votre attention.</p>
          <p>Nous allons maintenant revenir à l'accueil.</p>
        `,
        title: "Fin du tour"
      }
    ],
    nextLabel: 'Continuer',
    doneLabel: 'Continuer',
    showBullets: false,
    showProgress: false,
    disableInteraction: true
  });


  outro.oncomplete(() => {
    window.location.href = redirectUrl;
  });

  outro.onexit(() => {
    window.location.href = redirectUrl;
  });

  outro.start();
}
