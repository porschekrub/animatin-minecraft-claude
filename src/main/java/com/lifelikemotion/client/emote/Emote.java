package com.lifelikemotion.client.emote;

/** The emotes on the wheel. Duration in ticks; -1 = until you move. */
public enum Emote {
    WAVE(50), CLAP(50), CHEER(50), POINT(40), BOW(36), FACEPALM(46), DANCE(-1), SIT(-1);

    public final int duration;

    Emote(int duration) {
        this.duration = duration;
    }

    public String key() {
        return "emote.lifelikemotion." + name().toLowerCase();
    }

    public static Emote byId(int id) {
        Emote[] v = values();
        return id >= 0 && id < v.length ? v[id] : null;
    }
}
