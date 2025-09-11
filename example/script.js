// Test Infotainment UI JavaScript

class MusicPlayer {
    constructor() {
        this.isPlaying = false;
        this.currentTrack = 0;
        this.tracks = [
            { title: "Track 1", artist: "Artist 1" },
            { title: "Track 2", artist: "Artist 2" },
            { title: "Track 3", artist: "Artist 3" }
        ];
    }

    playPause() {
        this.isPlaying = !this.isPlaying;
        console.log(this.isPlaying ? 'Playing' : 'Paused');
        // Missing ARIA labels for screen readers
    }

    nextTrack() {
        this.currentTrack = (this.currentTrack + 1) % this.tracks.length;
        console.log('Next track:', this.tracks[this.currentTrack]);
        // Missing ARIA announcements
    }

    prevTrack() {
        this.currentTrack = this.currentTrack === 0 ? this.tracks.length - 1 : this.currentTrack - 1;
        console.log('Previous track:', this.tracks[this.currentTrack]);
        // Missing ARIA announcements
    }
}

class Navigation {
    constructor() {
        this.destination = '';
    }

    setDestination(destination) {
        this.destination = destination;
        console.log('Destination set:', destination);
        // Missing form validation feedback
    }

    navigate() {
        if (!this.destination) {
            alert('Please enter a destination');
            return;
        }
        console.log('Navigating to:', this.destination);
        // Missing loading states and progress feedback
    }
}

// Initialize components
const musicPlayer = new MusicPlayer();
const navigation = new Navigation();

// Global functions for HTML onclick handlers
function playPause() {
    musicPlayer.playPause();
}

function nextTrack() {
    musicPlayer.nextTrack();
}

function prevTrack() {
    musicPlayer.prevTrack();
}

// Form handling
document.addEventListener('DOMContentLoaded', function() {
    const form = document.querySelector('form');
    const input = document.querySelector('input[name="destination"]');
    
    if (form && input) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            navigation.setDestination(input.value);
            navigation.navigate();
        });
    }
});

// Keyboard navigation support
document.addEventListener('keydown', function(e) {
    switch(e.key) {
        case ' ':
            e.preventDefault();
            playPause();
            break;
        case 'ArrowRight':
            nextTrack();
            break;
        case 'ArrowLeft':
            prevTrack();
            break;
    }
});

// Focus management for accessibility
function setFocus(element) {
    if (element) {
        element.focus();
    }
}

// Screen reader announcements
function announceToScreenReader(message) {
    const announcement = document.createElement('div');
    announcement.setAttribute('aria-live', 'polite');
    announcement.setAttribute('aria-atomic', 'true');
    announcement.style.position = 'absolute';
    announcement.style.left = '-10000px';
    announcement.style.width = '1px';
    announcement.style.height = '1px';
    announcement.style.overflow = 'hidden';
    announcement.textContent = message;
    document.body.appendChild(announcement);
    
    setTimeout(() => {
        document.body.removeChild(announcement);
    }, 1000);
}
