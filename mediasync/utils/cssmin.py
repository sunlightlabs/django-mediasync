#!/usr/bin/env python
"""
* THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING 
* BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND 
* NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, 
* DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
* OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
* --
*
* @package 	cssmin
* @author 		Joe Scylla <joe.scylla@gmail.com>
* @copyright 	2008 Joe Scylla <joe.scylla@gmail.com>
* @license 	http://opensource.org/licenses/mit-license.php MIT License
* @version 	1.0 (2008-01-31)
"""
import re

def cssmin(css, out=None):
    
    css = css.strip()
    css = re.sub(r"\r\n", r"\n", css)
    
    css = re.sub(r"\/\*[\d\D]*?\*\/|\t+", r"", css)
    css = re.sub(r"\s+", r" ", css)
    css = re.sub(r"\}\s+", r"}\n", css)
    
    css = re.sub(r"\\;\s", r";", css)
    css = re.sub(r"\s+\{\\s+", r"{", css)
    css = re.sub(r"\\:\s+\\#", r":#", css)
    css = re.sub(r"(?i),\s+", r",", css)
    css = re.sub(r"(?i)\\:\s+\\\'", r":\'", css)
    css = re.sub(r"(?i)\\:\s+([0-9]+|[A-F]+)", r":\1", css)
    
    css = re.sub(r"\n", r"", css)

    if out:
        out.write(css)
    else:
        return css

if __name__ == '__main__':
    import sys
    cssmin(sys.stdin.read(), sys.stdout)