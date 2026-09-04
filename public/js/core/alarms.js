/**
 * CuraAssist Alarms Engine
 * Background medication schedule monitor with Web Audio API chime generator
 */
const AppAlarms = {
  intervalId: null,
  activeAlarmId: null,
  audioContext: null,

  start() {
    if (this.intervalId) return;
    this.intervalId = setInterval(() => this.check(), 1000);
    console.log('[AppAlarms] Background medication reminder daemon started.');
  },

  stop() {
    if (this.intervalId) {
      clearInterval(this.intervalId);
      this.intervalId = null;
    }
  },

  check() {
    const schedules = (typeof AppState !== 'undefined' && AppState.schedules) || (typeof state !== 'undefined' && state.schedules);
    if (!schedules || !Array.isArray(schedules)) return;

    const now = new Date();
    let hours = now.getHours();
    const minutes = String(now.getMinutes()).padStart(2, '0');
    const ampm = hours >= 12 ? 'PM' : 'AM';
    hours = hours % 12;
    hours = hours ? hours : 12; // 12-hour format
    const currentTimeStr = `${String(hours).padStart(2, '0')}:${minutes} ${ampm}`;

    schedules.forEach(item => {
      if (!item.taken && item.time === currentTimeStr && this.activeAlarmId !== item.id) {
        this.trigger(item);
      }
    });
  },

  trigger(schedule) {
    this.activeAlarmId = schedule.id;
    this.playChime();

    if (typeof AppEvents !== 'undefined') {
      AppEvents.emit('medication:due', schedule);
    }
    // Backward compatibility fallback to legacy global handler
    if (typeof triggerMedicationAlarm === 'function') {
      triggerMedicationAlarm(schedule);
    }
  },

  playChime() {
    try {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      if (!AudioCtx) return;
      if (!this.audioContext) this.audioContext = new AudioCtx();

      const ctx = this.audioContext;
      if (ctx.state === 'suspended') ctx.resume();

      // Dual-tone harmonic chime
      const osc1 = ctx.createOscillator();
      const osc2 = ctx.createOscillator();
      const gain = ctx.createGain();

      osc1.type = 'sine';
      osc1.frequency.setValueAtTime(587.33, ctx.currentTime); // D5
      osc1.frequency.exponentialRampToValueAtTime(880, ctx.currentTime + 0.3); // A5

      osc2.type = 'triangle';
      osc2.frequency.setValueAtTime(880, ctx.currentTime); // A5
      osc2.frequency.exponentialRampToValueAtTime(1174.66, ctx.currentTime + 0.3); // D6

      gain.gain.setValueAtTime(0.15, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.8);

      osc1.connect(gain);
      osc2.connect(gain);
      gain.connect(ctx.destination);

      osc1.start(ctx.currentTime);
      osc2.start(ctx.currentTime);
      osc1.stop(ctx.currentTime + 0.8);
      osc2.stop(ctx.currentTime + 0.8);
    } catch (e) {
      console.warn('[AppAlarms] Web Audio chime note:', e);
    }
  },

  dismiss(id) {
    if (this.activeAlarmId === id) {
      this.activeAlarmId = null;
    }
  }
};

if (typeof window !== 'undefined') {
  window.AppAlarms = AppAlarms;
}
