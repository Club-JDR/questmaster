var Konami = new Konami(function() {
    anime({
        targets: 'main',
        translateX: 10,
        autoplay: true,
        loop: false,
        easing: 'easeInOutSine',
        direction: 'alternate',
        scale: [{
            value: 1
        }, {
            value: 1.4
        }, {
            value: 1,
            delay: 250
        }],
        rotateY: {
            value: '+=180',
            delay: 200
        },
    });
});