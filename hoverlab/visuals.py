"""Bounded animation using only computed trajectory samples."""
from io import BytesIO
from PIL import Image, ImageDraw
import numpy as np

def animation(runs):
    frames=[]
    ymax=max(3.0,*(float(d.altitude.max())+0.5 for d in runs.values()))
    indices=np.linspace(0,len(runs['P'])-1,90,dtype=int)
    for k in indices:
        im=Image.new('RGB',(620,320),'#101c30'); draw=ImageDraw.Draw(im)
        draw.text((20,14),'HOVERLAB | SIMULATION ONLY',fill='white')
        draw.text((20,35),f'Time: {runs["P"].time.iloc[k]:.1f} s | height scale: 0–{ymax:.1f} m',fill='white')
        for x,(kind,df),color in zip((170,450),runs.items(),('#ffbd66','#60d5df')):
            z=float(df.altitude.iloc[k]); y=270-int(z/ymax*190)
            ty=270-int(float(df.target.iloc[k])/ymax*190)
            draw.line((x-100,ty,x+100,ty), fill='#94a3b8',width=2)
            draw.line((x-100,270,x+100,270),fill='white',width=2)
            draw.line((x-30,y,x+30,y),fill=color,width=5)
            draw.ellipse((x-43,y-8,x-15,y+2),outline=color,width=3)
            draw.ellipse((x+15,y-8,x+43,y+2),outline=color,width=3)
            draw.rectangle((x-9,y-5,x+9,y+8),fill=color)
            draw.text((x-55,290),f'{kind}: {z:.2f} m',fill=color)
        frames.append(im)
    out=BytesIO(); frames[0].save(out,format='GIF',save_all=True,append_images=frames[1:],duration=90,loop=0)
    return out.getvalue()
