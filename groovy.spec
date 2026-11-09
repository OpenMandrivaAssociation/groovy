Name:		groovy
Version:	3.0.22
Release:	1
Summary:	Agile and dynamic language for the Java platform
Group:		Development/Java
# Console icons under groovy/ui/icons are the famfamfam Silk set (CC-BY).
License:	ASL 2.0 and CC-BY
URL:		https://groovy-lang.org/
# Tag GROOVY_3_0_22. The gradle-wrapper jar and a test-resources jar are
# removed from this archive; nothing here is a prebuilt class file.
Source0:	https://github.com/apache/groovy/archive/refs/tags/GROOVY_3_0_22.tar.gz#/groovy-%{version}.tar.gz
# Parrot parser against antlr4-runtime 4.13: clearDfaCache, BaseErrorListener,
# notifyErrorListeners(Token, String, RecognitionException). AstBuilder keeps
# calling the shared context getter (type(), expression(), primary(), ...).
Patch0:		groovy-3.0.22-antlr413.patch
# javax.swing.JApplet is gone from this JDK. Drop the applet entry points.
# void run() still opens the frame console. CST inspect still extends TestRig.
Patch1:		groovy-3.0.22-jdk27-console.patch

BuildArch:	noarch
BuildRequires:	java-current-devel
BuildRequires:	sysjar
# 4.13.2-2 names context getters after the referenced rule. 4.13.2-4
# follows the shared name, lets a List getter win, and ships TestRig.
BuildRequires:	antlr4-tool >= 4.13.2-4
BuildRequires:	mvn(antlr:antlr)
BuildRequires:	mvn(org.antlr:antlr4-runtime)
BuildRequires:	mvn(org.ow2.asm:asm)
BuildRequires:	mvn(org.ow2.asm:asm-analysis)
BuildRequires:	mvn(org.ow2.asm:asm-commons)
BuildRequires:	mvn(org.ow2.asm:asm-tree)
BuildRequires:	mvn(org.ow2.asm:asm-util)
BuildRequires:	mvn(info.picocli:picocli)
BuildRequires:	mvn(com.thoughtworks.xstream:xstream)
BuildRequires:	mvn(org.apache.ivy:ivy)
BuildRequires:	mvn(org.fusesource.jansi:jansi)
BuildRequires:	mvn(junit:junit)
BuildRequires:	mvn(com.github.javaparser:javaparser-core)
BuildRequires:	mvn(org.apache.ant:ant)
BuildRequires:	mvn(org.apache.ant:ant-launcher)
BuildRequires:	mvn(org.abego.treelayout:org.abego.treelayout.core)

%description
Groovy compiles to Java bytecode and calls Java libraries directly.
Gradle 8.11.1's default distribution (bundleGroovy4 off) APIs thirteen
org.codehaus.groovy 3.0.22 modules: groovy, groovy-ant, groovy-astbuilder,
groovy-console, groovy-datetime, groovy-dateutil, groovy-groovydoc,
groovy-json, groovy-nio, groovy-sql, groovy-templates, groovy-test and
groovy-xml. This package also ships groovy-swing, which the console
module links. ASM, ANTLR and picocli stay separate system jars.

%prep
%autosetup -n groovy-GROOVY_3_0_22 -p1
find . -name '*.jar' -delete

%build
set -eo pipefail
export JAVA_HOME=%{_jvmdir}/java-openjdk
export PATH=$JAVA_HOME/bin:$PATH

WORK=$PWD/work
rm -rf "$WORK"
mkdir -p "$WORK/stubs/javax/annotation/concurrent" \
	"$WORK/stubs/edu/umd/cs/findbugs/annotations" \
	"$WORK/gen/antlr2/org/codehaus/groovy/antlr/parser" \
	"$WORK/gen/antlr2/org/codehaus/groovy/antlr/java" \
	"$WORK/gen/antlr4/org/apache/groovy/parser/antlr4" \
	"$WORK/classes" "$WORK/dgm/META-INF"

# SOURCE-retention only. Compiled for the compiler, never packed into a jar.
cat > "$WORK/stubs/javax/annotation/Nullable.java" <<'END'
package javax.annotation;
import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;
@Retention(RetentionPolicy.SOURCE)
@Target({ElementType.FIELD, ElementType.METHOD, ElementType.PARAMETER, ElementType.LOCAL_VARIABLE, ElementType.TYPE_USE})
public @interface Nullable {}
END
cat > "$WORK/stubs/javax/annotation/concurrent/GuardedBy.java" <<'END'
package javax.annotation.concurrent;
import java.lang.annotation.*;
@Retention(RetentionPolicy.SOURCE)
public @interface GuardedBy { String value(); }
END
cat > "$WORK/stubs/javax/annotation/concurrent/Immutable.java" <<'END'
package javax.annotation.concurrent;
import java.lang.annotation.*;
@Retention(RetentionPolicy.SOURCE)
public @interface Immutable {}
END
cat > "$WORK/stubs/javax/annotation/concurrent/ThreadSafe.java" <<'END'
package javax.annotation.concurrent;
import java.lang.annotation.*;
@Retention(RetentionPolicy.SOURCE)
public @interface ThreadSafe {}
END
cat > "$WORK/stubs/javax/annotation/concurrent/NotThreadSafe.java" <<'END'
package javax.annotation.concurrent;
import java.lang.annotation.*;
@Retention(RetentionPolicy.SOURCE)
public @interface NotThreadSafe {}
END
cat > "$WORK/stubs/edu/umd/cs/findbugs/annotations/SuppressFBWarnings.java" <<'END'
package edu.umd.cs.findbugs.annotations;
import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;
@Retention(RetentionPolicy.SOURCE)
@Target({ElementType.TYPE, ElementType.FIELD, ElementType.METHOD, ElementType.CONSTRUCTOR, ElementType.PARAMETER})
public @interface SuppressFBWarnings {
    String[] value() default {};
    String justification() default "";
}
END
find "$WORK/stubs" -name '*.java' > "$WORK/stub-sources.list"
javac --release 8 -encoding UTF-8 -Xlint:-options -d "$WORK/stub-classes" @"$WORK/stub-sources.list"

# jansi's jar is /usr/lib/java on every cooker arch, not %%{_libdir}.
JANSI=/usr/lib/java/jansi/jansi.jar
IVY=%{_javadir}/ivy.jar
JUNIT=%{_javadir}/junit.jar
JAVAPARSER=%{_javadir}/javaparser-core.jar
TREE=%{_javadir}/treelayout/org.abego.treelayout.core.jar
test -f "$JANSI" -a -f "$IVY" -a -f "$JUNIT" -a -f "$JAVAPARSER" -a -f "$TREE"

BASE_CP="$WORK/stub-classes"
for j in \
	%{_javadir}/antlr.jar \
	%{_javadir}/antlr4-runtime.jar \
	%{_javadir}/asm.jar \
	%{_javadir}/asm-analysis.jar \
	%{_javadir}/asm-commons.jar \
	%{_javadir}/asm-tree.jar \
	%{_javadir}/asm-util.jar \
	%{_javadir}/picocli.jar \
	%{_javadir}/xstream.jar \
	"$IVY" \
	"$JANSI"
do
	BASE_CP="$BASE_CP:$j"
done

java -cp %{_javadir}/antlr.jar antlr.Tool \
	-o "$WORK/gen/antlr2/org/codehaus/groovy/antlr/parser" \
	src/main/antlr2/org/codehaus/groovy/antlr/groovy.g
java -cp %{_javadir}/antlr.jar antlr.Tool \
	-o "$WORK/gen/antlr2/org/codehaus/groovy/antlr/java" \
	src/main/antlr2/org/codehaus/groovy/antlr/java/java.g

# GroovyParser.g4 looks for GroovyLexer.tokens beside the grammar.
(
	cd src/antlr
	antlr4 -visitor -no-listener -package org.apache.groovy.parser.antlr4 GroovyLexer.g4
	antlr4 -visitor -no-listener -package org.apache.groovy.parser.antlr4 GroovyParser.g4
)
find src/antlr -maxdepth 1 -name 'Groovy*.java' -exec /bin/mv -f {} "$WORK/gen/antlr4/org/apache/groovy/parser/antlr4/" \;
rm -f src/antlr/Groovy*.tokens src/antlr/Groovy*.interp

find src/main/java -name '*.java' ! -path '*/vmplugin/v9/*' > "$WORK/core-java.list"
find "$WORK/gen" -name '*.java' >> "$WORK/core-java.list"
find subprojects/parser-antlr4/src/main/java -name '*.java' >> "$WORK/core-java.list"
javac --release 8 -encoding UTF-8 -Xlint:-options -cp "$BASE_CP" -d "$WORK/classes" @"$WORK/core-java.list"
find src/main/java/org/codehaus/groovy/vmplugin/v9 -name '*.java' > "$WORK/v9.list"
javac --release 11 -encoding UTF-8 -Xlint:-options -cp "$WORK/classes:$BASE_CP" -d "$WORK/classes" @"$WORK/v9.list"
/bin/cp -a src/resources/. "$WORK/classes/"

java -cp "$WORK/classes:$BASE_CP" org.codehaus.groovy.tools.DgmConverter --info "$WORK/dgm"
/bin/cp -a "$WORK/dgm/." "$WORK/classes/"

find src/main/groovy -name '*.groovy' > "$WORK/core-groovy.list"
GROOVY_CP="$WORK/classes:$BASE_CP"
java -cp "$GROOVY_CP" org.codehaus.groovy.tools.FileSystemCompiler \
	--classpath "$GROOVY_CP" -d "$WORK/groovy-classes" @"$WORK/core-groovy.list"
/bin/cp -a "$WORK/groovy-classes/." "$WORK/classes/"

CORE_CP="$WORK/classes:$BASE_CP"
mkdir -p "$WORK/mods"

write_descriptor() {
	out=$1
	name=$2
	ext=$3
	static_ext=$4
	mkdir -p "$out/META-INF/groovy"
	cat > "$out/META-INF/groovy/org.codehaus.groovy.runtime.ExtensionModule" <<EOF
moduleName=${name}
moduleVersion=%{version}
extensionClasses=${ext}
staticExtensionClasses=${static_ext}
EOF
}

compile_mod() {
	name=$1
	shift
	extra_cp=$1
	shift
	mode=${1:-plain}
	out=$WORK/mods/$name
	rm -rf "$out"
	mkdir -p "$out"
	jlist=$WORK/$name.java.list
	glist=$WORK/$name.groovy.list
	: > "$jlist"
	: > "$glist"
	if [ -d "subprojects/$name/src/main/java" ]; then
		find "subprojects/$name/src/main/java" -name '*.java' >> "$jlist"
	fi
	if [ -d "subprojects/$name/src/main/groovy" ]; then
		find "subprojects/$name/src/main/groovy" -name '*.java' >> "$jlist"
		find "subprojects/$name/src/main/groovy" -name '*.groovy' >> "$glist"
	fi
	cp="$CORE_CP:$extra_cp"
	if [ "$mode" = joint ]; then
		# -J-release=8 is passed through as javac --release 8.
		cat "$jlist" "$glist" > "$WORK/$name.joint.list"
		java -cp "$cp" org.codehaus.groovy.tools.FileSystemCompiler \
			--classpath "$cp" -d "$out" -j -J-release=8 -Jencoding=UTF-8 \
			-FXlint:-options @"$WORK/$name.joint.list"
	else
		if [ -s "$jlist" ]; then
			javac --release 8 -encoding UTF-8 -Xlint:-options -cp "$cp" -d "$out" @"$jlist"
		fi
		if [ -s "$glist" ]; then
			java -cp "$out:$cp" org.codehaus.groovy.tools.FileSystemCompiler \
				--classpath "$out:$cp" -d "$out" @"$glist"
		fi
	fi
	if [ -d "subprojects/$name/src/main/resources" ]; then
		/bin/cp -a "subprojects/$name/src/main/resources/." "$out/"
	fi
	rm -rf "$out/edu" "$out/javax/annotation"
	echo "$name $(find "$out" -name '*.class' | wc -l)"
}

compile_mod groovy-astbuilder ""
compile_mod groovy-datetime ""
write_descriptor "$WORK/mods/groovy-datetime" groovy-datetime \
	org.apache.groovy.datetime.extensions.DateTimeExtensions \
	org.apache.groovy.datetime.extensions.DateTimeStaticExtensions
compile_mod groovy-dateutil ""
write_descriptor "$WORK/mods/groovy-dateutil" groovy-dateutil \
	org.apache.groovy.dateutil.extensions.DateUtilExtensions \
	org.apache.groovy.dateutil.extensions.DateUtilStaticExtensions
compile_mod groovy-nio ""
write_descriptor "$WORK/mods/groovy-nio" groovy-nio \
	org.apache.groovy.nio.extensions.NioExtensions ""
compile_mod groovy-json ""
compile_mod groovy-sql ""
write_descriptor "$WORK/mods/groovy-sql" groovy-sql \
	org.apache.groovy.sql.extensions.SqlExtensions ""
compile_mod groovy-xml ""
write_descriptor "$WORK/mods/groovy-xml" groovy-xml \
	org.apache.groovy.xml.extensions.XmlExtensions ""
compile_mod groovy-swing ""
write_descriptor "$WORK/mods/groovy-swing" groovy-swing \
	org.apache.groovy.swing.extensions.SwingExtensions ""
compile_mod groovy-templates "$WORK/mods/groovy-xml"
compile_mod groovy-test "$JUNIT"
compile_mod groovy-groovydoc "$WORK/mods/groovy-xml:$WORK/mods/groovy-templates:$JAVAPARSER"
mkdir -p "$WORK/mods/groovy-groovydoc/org/apache/groovy/docgenerator"
/bin/cp -f subprojects/groovy-docgenerator/src/main/resources/org/apache/groovy/docgenerator/groovy.ico \
	"$WORK/mods/groovy-groovydoc/org/apache/groovy/docgenerator/groovy.ico"
compile_mod groovy-ant "$WORK/mods/groovy-groovydoc:%{_javadir}/ant.jar:%{_javadir}/ant-launcher.jar"
compile_mod groovy-console "$WORK/mods/groovy-xml:$WORK/mods/groovy-swing:$WORK/mods/groovy-templates:%{_javadir}/antlr4-tool.jar:$TREE" joint

jar cf groovy.jar -C "$WORK/classes" .
for name in groovy-ant groovy-astbuilder groovy-console groovy-datetime groovy-dateutil \
	groovy-groovydoc groovy-json groovy-nio groovy-sql groovy-swing groovy-templates \
	groovy-test groovy-xml
do
	jar cf "$name.jar" -C "$WORK/mods/$name" .
done

dep() {
	echo "    <dependency>"
	echo "      <groupId>$1</groupId>"
	echo "      <artifactId>$2</artifactId>"
	echo "      <version>$3</version>"
	echo "    </dependency>"
}

write_pom() {
	artifact=$1
	shift
	{
		echo '<?xml version="1.0" encoding="UTF-8"?>'
		echo '<project xmlns="http://maven.apache.org/POM/4.0.0">'
		echo '  <modelVersion>4.0.0</modelVersion>'
		echo '  <groupId>org.codehaus.groovy</groupId>'
		echo "  <artifactId>${artifact}</artifactId>"
		echo '  <version>%{version}</version>'
		echo "  <name>${artifact}</name>"
		echo '  <description>Groovy %{version}, built from source against system libraries.</description>'
		echo '  <url>https://groovy-lang.org/</url>'
		echo '  <licenses>'
		echo '    <license>'
		echo '      <name>Apache License, Version 2.0</name>'
		echo '      <url>https://www.apache.org/licenses/LICENSE-2.0.txt</url>'
		echo '    </license>'
		echo '  </licenses>'
		if [ "$#" -gt 0 ]; then
			echo '  <dependencies>'
			while [ "$#" -gt 0 ]; do
				dep "$1" "$2" "$3"
				shift 3
			done
			echo '  </dependencies>'
		fi
		echo '</project>'
	} > "$artifact.pom"
}

write_pom groovy \
	org.ow2.asm asm 9.11.1 \
	org.ow2.asm asm-analysis 9.11.1 \
	org.ow2.asm asm-commons 9.11.1 \
	org.ow2.asm asm-tree 9.11.1 \
	org.ow2.asm asm-util 9.11.1 \
	antlr antlr 2.7.7 \
	org.antlr antlr4-runtime 4.13.2 \
	info.picocli picocli 4.7.7 \
	com.thoughtworks.xstream xstream 1.4.21 \
	org.apache.ivy ivy 2.6.0 \
	org.fusesource.jansi jansi 2.4.2
write_pom groovy-ant \
	org.codehaus.groovy groovy %{version} \
	org.apache.ant ant 1.10.18 \
	org.apache.ant ant-launcher 1.10.18 \
	org.codehaus.groovy groovy-groovydoc %{version}
write_pom groovy-astbuilder org.codehaus.groovy groovy %{version}
write_pom groovy-console \
	org.codehaus.groovy groovy %{version} \
	org.codehaus.groovy groovy-swing %{version} \
	org.codehaus.groovy groovy-templates %{version} \
	org.codehaus.groovy groovy-xml %{version} \
	org.antlr antlr4 4.13.2 \
	org.abego.treelayout org.abego.treelayout.core 1.0.3
write_pom groovy-datetime org.codehaus.groovy groovy %{version}
write_pom groovy-dateutil org.codehaus.groovy groovy %{version}
write_pom groovy-groovydoc \
	org.codehaus.groovy groovy %{version} \
	org.codehaus.groovy groovy-templates %{version} \
	org.codehaus.groovy groovy-xml %{version} \
	com.github.javaparser javaparser-core 3.28.2
write_pom groovy-json org.codehaus.groovy groovy %{version}
write_pom groovy-nio org.codehaus.groovy groovy %{version}
write_pom groovy-sql org.codehaus.groovy groovy %{version}
write_pom groovy-swing org.codehaus.groovy groovy %{version}
write_pom groovy-templates \
	org.codehaus.groovy groovy %{version} \
	org.codehaus.groovy groovy-xml %{version}
write_pom groovy-test \
	org.codehaus.groovy groovy %{version} \
	junit junit 4.13.2
write_pom groovy-xml org.codehaus.groovy groovy %{version}

%check
set -eo pipefail
export JAVA_HOME=%{_jvmdir}/java-openjdk
export PATH=$JAVA_HOME/bin:$PATH
JANSI=/usr/lib/java/jansi/jansi.jar
CP="%{_javadir}/antlr.jar:%{_javadir}/antlr4-runtime.jar:%{_javadir}/asm.jar:%{_javadir}/asm-analysis.jar:%{_javadir}/asm-commons.jar:%{_javadir}/asm-tree.jar:%{_javadir}/asm-util.jar:%{_javadir}/picocli.jar:%{_javadir}/xstream.jar:%{_javadir}/ivy.jar:$JANSI"
cat > Smoke.groovy <<'END'
class Box { int n }
def b = new Box(n: 40)
def m = [a: [b: 2]]
println "groovy_ok ${b.n + m.a.b}"
END
test "$(java -cp groovy.jar:$CP groovy.ui.GroovyMain Smoke.groovy)" = "groovy_ok 42"
cat > XmlSmoke.groovy <<'END'
def x = new XmlSlurper().parseText('<a>ok</a>')
println "xml_ok ${x}"
END
test "$(java -cp groovy.jar:groovy-xml.jar:$CP groovy.ui.GroovyMain XmlSmoke.groovy)" = "xml_ok ok"
jar tf groovy.jar | grep -q 'META-INF/dgminfo'
jar tf groovy-groovydoc.jar | grep -q 'org/apache/groovy/docgenerator/groovy.ico'
jar tf groovy-json.jar | grep -q 'META-INF/services/org.apache.groovy.json.FastStringServiceFactory'
for name in groovy-datetime groovy-dateutil groovy-nio groovy-sql groovy-xml groovy-swing; do
	jar tf "$name.jar" | grep -q 'META-INF/groovy/org.codehaus.groovy.runtime.ExtensionModule'
done
for j in groovy.jar groovy-*.jar; do
	if jar tf "$j" | grep -E '^(edu/umd|javax/annotation)/'; then
		echo "annotation stub leaked into $j"
		exit 1
	fi
done

%install
# No -u: rpm's install trailer reads DONT_CLEANUP, which is unset.
set -eo pipefail
sysjar install --buildroot %{buildroot} \
	--artifact groovy.pom:groovy.jar \
	--file-name groovy \
	--filelist .mfiles
for name in groovy-ant groovy-astbuilder groovy-console groovy-datetime groovy-dateutil \
	groovy-groovydoc groovy-json groovy-nio groovy-sql groovy-swing groovy-templates \
	groovy-test groovy-xml
do
	sysjar install --buildroot %{buildroot} \
		--artifact "$name.pom:$name.jar" \
		--file-name "$name" \
		--filelist ".mfiles-$name"
	grep -v '%%dir /usr/share/sysjar/index/org.codehaus.groovy' ".mfiles-$name" >> .mfiles
done

%files -f .mfiles
%doc LICENSE NOTICE README.adoc
