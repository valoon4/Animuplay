package de.minimal.musicplayer;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.util.AttributeSet;
import android.view.MotionEvent;
import android.view.View;

/** Lightweight A-Z index for quickly jumping through large sorted lists. */
public final class AlphabetIndexView extends View {
    private static final String[] LABELS = {
            "#", "A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M",
            "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z"
    };

    public interface OnLetterSelectedListener {
        void onLetterSelected(String letter);
    }

    private final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private OnLetterSelectedListener listener;
    private int lastIndex = -1;

    public AlphabetIndexView(Context context) {
        this(context, null);
    }

    public AlphabetIndexView(Context context, AttributeSet attrs) {
        super(context, attrs);
        paint.setColor(context.getColor(R.color.accent));
        paint.setTextAlign(Paint.Align.CENTER);
        paint.setFakeBoldText(true);
        setContentDescription("Alphabetischer Schnellsprung");
    }

    public void setOnLetterSelectedListener(OnLetterSelectedListener listener) {
        this.listener = listener;
    }

    @Override
    protected void onDraw(Canvas canvas) {
        super.onDraw(canvas);
        if (getHeight() <= 0 || getWidth() <= 0) return;
        float slot = getHeight() / (float) LABELS.length;
        paint.setTextSize(Math.max(8f, Math.min(dp(11), slot * 0.72f)));
        Paint.FontMetrics metrics = paint.getFontMetrics();
        float baselineOffset = -(metrics.ascent + metrics.descent) / 2f;
        float x = getWidth() / 2f;
        for (int index = 0; index < LABELS.length; index++) {
            float y = slot * (index + 0.5f) + baselineOffset;
            canvas.drawText(LABELS[index], x, y, paint);
        }
    }

    @Override
    public boolean onTouchEvent(MotionEvent event) {
        int action = event.getActionMasked();
        if (action != MotionEvent.ACTION_DOWN && action != MotionEvent.ACTION_MOVE
                && action != MotionEvent.ACTION_UP) {
            return super.onTouchEvent(event);
        }
        if (getHeight() <= 0) return true;
        int index = (int) (event.getY() / getHeight() * LABELS.length);
        index = Math.max(0, Math.min(LABELS.length - 1, index));
        if (index != lastIndex || action == MotionEvent.ACTION_DOWN) {
            lastIndex = index;
            if (listener != null) listener.onLetterSelected(LABELS[index]);
        }
        if (action == MotionEvent.ACTION_UP) lastIndex = -1;
        return true;
    }

    private int dp(int value) {
        return Math.round(value * getResources().getDisplayMetrics().density);
    }
}
